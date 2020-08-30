import json
import os
import hmac
import hashlib
from urllib.parse import parse_qs
import random
from src.dynamo_db_helper import *
import boto3

HEADMASTER = ['dianapatrong', 'bellatrix']
HOGWARTS_HOUSES = ['gryffindor', 'slytherin', 'ravenclaw', 'hufflepuff']
PREFIXES = ["In the lead is ", "Second place is ", "Third place is ", "Fourth place is "]
# CHANNEL_ID = os.environ['CHANNEL_ID']
INSTRUCTIONS = {
    '- set house': '/dumbledore set house house_name _*or*_ /dumbledore set house :sorting-hat:\n',
    '- set title': '/dumbledore set title your name and whatever you wanna be called like Hogwarts Caretaker, be creative\n',
    '- leaderboard': '/dumbledore leaderboard\n',
    '- house leaderboard': '/dumbledore house_name\n',
    '- give points': '/dumbledore give 10 points to @wizard _*or*_ /dumbledore +10 @wizard\n',
    '- remove points': '/dumbledore remove 10 points from @wizard _*or*_ /dumbledore -10 @wizard\n\n',
    'HINT': f' House names are  _*{", ".join(HOGWARTS_HOUSES)}*_,  but if you are not sure which house do you'
            f' belong to, you can set it to :sorting-hat: and that will do the job'
}


def verify_request(event):
    body = event['body']
    timestamp = event['headers']['X-Slack-Request-Timestamp']
    slack_signature = event['headers']['X-Slack-Signature']
    sig_basestring = f"v0:{timestamp}:{body}".encode('utf-8')
    my_signature = f"v0={hmac.new(os.environ['SLACK_KEY'].encode('utf-8'), sig_basestring, hashlib.sha256).hexdigest()}"
    return hmac.compare_digest(my_signature, slack_signature)


def respond(message=None):
    message['response_type'] = 'in_channel'
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }


def remove_at(name):
    return name.replace('@', '').lower()


def parse_points(text, give_points):
    possible_points = []
    for num in text:
        try:
            possible_points.append(int(num))
        except ValueError:
            print("Not an integer")

    if not possible_points and give_points:
        points = 200  # Default value if not given any points
    elif not give_points:
        points = -possible_points[0] if possible_points[0] > 0 else possible_points[0]
    else:
        points = possible_points[0]
    return points


def parse_slack_message(text):
    give_points = True if [word for word in text if any(s in word for s in ['give', '+'])] else False
    wizards = [remove_at(name) for name in text if name.startswith('@')]
    if not wizards:
        return False, False
    else:
        points = parse_points(text, give_points)
        return wizards, points


def get_house_points(table, house):
    scanned_wizards = scan_info(table, house)
    total_points = int(sum([wizard['points'] for wizard in scanned_wizards]))
    house_members = {}
    for wizard in scanned_wizards:
        house_members[get_title_if_exists_dict(wizard)] = wizard['points']

    members_by_points = {member: house_members[member] for member in sorted(house_members, key=house_members.get, reverse=True)}

    house_members_leaderboard = ""
    for member, points in members_by_points.items():
        house_members_leaderboard += f'_{member}_: {points}\n'

    return total_points, house_members_leaderboard


def format_points(house_points):
    order_by_points = {house: house_points[house] for house in sorted(house_points, key=house_points.get, reverse=True)}
    houses_leaderboard = ""
    for prefix, (house, points) in zip(PREFIXES, order_by_points.items()):
        houses_leaderboard += f'_{prefix}*{house.capitalize()}* with *{points}* points_\n'
    return houses_leaderboard


def get_house_leaderboard(table):
    house_points = {}
    for house in HOGWARTS_HOUSES:
        scanned_wizards = scan_info(table, house)
        house_points[house] = int(sum([wizard['points'] for wizard in scanned_wizards]))
    return house_points


def parse_potential_house(house):
    target_house = house.lower()
    if target_house in HOGWARTS_HOUSES:
        return target_house
    else:
        return None


def create_wizard(table, wizard, house):
    wizard = remove_at(wizard)
    put_item(table, wizard, house)
    message = {'text': f'Welcome _*{wizard}*_ to _*{house}*_'}  # change username to full name eventually
    return message


def display_instructions():
    dumbledore_orders = ""
    for order, command in INSTRUCTIONS.items():
        dumbledore_orders += f'*{order}*: {command}'
    return dumbledore_orders


def clean_points(points):
    return max(-2000, points) if points < 0 else min(2000, points)


def get_wizard_points(table, wizard):
    wizard_info = get_item_info(table, wizard)
    points = int(wizard_info['points'])
    print("POPOPO INS", points)
    return points


def get_title_if_exists(table, wizard):
    wizard_info = get_item_info(table, wizard)
    return wizard_info['title'] if 'title' in wizard_info else wizard_info['username']


def get_title_if_exists_dict(wizard):
    return wizard['title'] if 'title' in wizard else wizard['username']


def allocate_points(table, wizard, points, assigner):
    points = clean_points(points)
    wizard_info = get_item_info(table, wizard)
    print("wizard_info", wizard_info)
    points_to_give = wizard_info['points'] + points

    update_points = update_item(
        table,
        wizard,
        attributes={':p': points_to_give},
        condition='attribute_exists(username)',
        update_expression='set points = :p',
        return_values='ALL_NEW'
    )
    print("update points", update_points)

    set_points_to_zero = update_item(
        table,
        wizard,
        attributes={':min': 0},
        condition='points < :min',
        update_expression='set points = :min',
        return_values='UPDATED_NEW'
    )
    print("updated_points", update_points)
    print("set_to_zero", set_points_to_zero)

    message = set_points_to_zero if set_points_to_zero else update_points
    total_points = message['Attributes']['points']
    print("total_points", total_points)
    assignee = get_title_if_exists(table, wizard)
    assigner = get_title_if_exists(table, assigner)
    points_action = f'awarded *{points}* points to *{assignee}*' if points > 0 else f'removed *{points}* points from *{wizard}*'
    message = {'text': f'_*{assigner}* has {points_action}, new total is *{total_points}* points_'}
    return message


def is_headmaster(wizard, assigner):
    return True if wizard == assigner and assigner not in HEADMASTER else False


def process_point_allocation2(table, assigner, text):
    message = {}
    wizards, points_to_give = parse_slack_message(text)
    agg_messages = []
    if wizards:
        for wizard in wizards:
            # Avoid wizards from granting points to themselves
            if is_headmaster(wizard, assigner):
                current_points = get_wizard_points(table, wizard)
                title = get_title_if_exists(table, wizard)

                message = {'text': f'_*{title}*_ has *{current_points}* points, cheater  '}
                message['attachments'] = [{'text': '_Are you awarding points to yourself? '
                                                   'That is like the *Forbidden Forest*: off limits_ :shame:'}]
            else:
                points_allocated = allocate_points(table, wizard, points_to_give, assigner)
                agg_messages.append(points_allocated) if points_allocated else False

        if agg_messages:
            message = {'text': '\n'.join(m_points['text'] for m_points in agg_messages)}
    else:
        message = {'text': f'_What do you think this is? Magic? '
                           f'I do not know which wizard do you want to give points to_'}
    return message


def process_point_allocation(table, wizards, points, assigner):
    message = {}
    agg_messages = []
    for wizard in wizards:
        # Avoid wizards from granting points to themselves
        if is_headmaster(wizard, assigner):
            current_points = get_wizard_points(table, wizard)
            title = get_title_if_exists(table, wizard)
            message = {'text': f'_*{title}*_ has *{current_points}* points, cheater  '}
            message['attachments'] = [{'text': '_Are you awarding points to yourself? '
                                               'That is like the *Forbidden Forest*: off limits_ :shame:'}]
        else:
            points_allocated = allocate_points(table, wizard, points, assigner)
            agg_messages.append(points_allocated) if points_allocated else False

    if agg_messages:
        message = {'text': '\n'.join(m_points['text'] for m_points in agg_messages)}
    return message


def parse_house_text(text):
    hogwarts_house = None
    if len(text) == 1:
        if text[0] == ':sorting-hat:':
            hogwarts_house = random.choice(HOGWARTS_HOUSES)
        else:
            hogwarts_house = parse_potential_house(text[0])
    return hogwarts_house


def set_wizards_title(table, title, wizard):
    wizard = remove_at(wizard)
    update_item(
        table,
        wizard,
        attributes={':t': title},
        update_expression='set title = :t',
        return_values="UPDATED_NEW"
    )
    if title:
        message = {'text': f'_Your title has been updated to *{title}*_'}
    else:
        message = {'text': f'_Give the instructions another read, maybe it takes twice to understand_'}
    return message


def send_random_quote(assigner):
    random_quotes = [
        'What happened down in the dungeons between you and Professor Quirrell is a complete secret, so, naturally the whole school knows.',
        'One can never have enough socks',
        f'It is our choices, *{assigner}*, that show what we truly are, far more than our abilities.',
        f'It is a curious thing, *{assigner}*, but perhaps those who are best suited to power are those who have never sought it.',
        'You will also find that help will always be given at Hogwarts to those who ask for it.',
        'Happiness can be found even in the darkest of times, when one only remembers to turn on the light.',
        f'Do not put your wand there, *{assigner}*! .. Better wizards than you have lost buttocks, you know.',
        f'Of course this is happening inside your head, *{assigner}*, but why on earth should that mean that it is not real?',
        'There are some things you cannot share without ending up liking each other, and knocking out a twelve-foot mountain troll is one of them.',
        'Never trust anything that can think for itself if you cannot see where it keeps its brain.'
    ]
    return {'text': f'_{random.choice(random_quotes)}_'}


def verify_user(table, user):
    return get_item_exists(table, user)


def lambda_handler(event, context):
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table('Hogwarts_Alumni')

    message = {}
    '''
    if not verify_request(event):
        return respond({"text":"Message verification failed"})
    '''

    params = parse_qs(event['body'])

    '''
    channel_id = params['channel_id']
    if channel_id[0] != CHANNEL_ID:  # This is only for locking the slash command to a single channel
        message = respond({'text': '_The *Marauder\'s Map* shows everyone, use it to find the slack channel where '
                                   'this feature is located_'})
        return message
    '''

    if 'text' in params:
        text = params['text'][0].replace('\xa0', ' ').split(" ")
        assigner = params['user_name'][0]
        point_allocators = ['give', 'remove', '+', '-']
        matching_words = [word for word in text if any(s in word for s in point_allocators)]

        if verify_user(table, assigner):
            # Display leaderboard for all houses
            if 'leaderboard' in text:
                house_points = get_house_leaderboard(table)
                message = {'text': f'{format_points(house_points)}'}

            # Display leaderboard for the house requested
            elif len(text) == 1 and text[0].lower() in HOGWARTS_HOUSES:
                house = text[0].lower()
                total_points, members_leaderboard = get_house_points(table, house)
                message = {'text': f'_*{house}*_ has *{total_points}* points',
                           'attachments': [{"text": members_leaderboard}]}

            elif ['set', 'house'] == text[0:2]:
                message = {'text': f'Wizard _*{assigner}*_ already exists'}

            elif ['set', 'title'] == text[0:2] and len(text) > 2:
                title = ' '.join(text[2:])
                message = set_wizards_title(table, title, assigner)

            # Allocate points
            elif matching_words:
                wizards, points = parse_slack_message(text)
                verified_wizards = [wizard for wizard in wizards if verify_user(table, wizard)]
                if verified_wizards:
                    message = process_point_allocation(table, verified_wizards, points, assigner)
                else:
                    message = {'text': f'_What do you think this is? Magic? '
                                       f'I do not know which wizard do you want to give points to_'}

            else:
                message = send_random_quote(assigner)
        else:
            # Set wizard to requested house
            if ['set', 'house'] == text[0:2]:
                house = parse_house_text(text[2:])
                if house is not None:
                    message = create_wizard(table, assigner, house)
            else:
                message = {'text': f'_Are you a *muggle* or what? Spell the house name correctly:'
                                   f' *{", ".join(HOGWARTS_HOUSES)}* or :sorting-hat:'}

                message = {'text': f'Wizard {assigner} is not enrolled yet'}
    else:
        instructions = display_instructions()
        message = {'text': f'First add yourself to your favorite house :european_castle:,  '
                           f'then you can start giving or taking points right away '
                           f':male_mage::skin-tone-2:  :deathly-hallows: ', 'attachments': [{"text": instructions}]}

    message['response_type'] = 'in_channel'

    return respond(message)



