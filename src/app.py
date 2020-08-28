import json
import os
import hmac
import hashlib
from urllib.parse import parse_qs
import random
from dynamo_db_helper import *


HEADMASTER = ['dianapatrong']
HOGWARTS_HOUSES = ['gryffindor', 'slytherin', 'ravenclaw', 'hufflepuff']
PREFIXES = ["In the lead is ", "Second place is ", "Third place is ", "Fourth place is "]


def verify_request(event):
    body = event['body']
    timestamp = event['headers']['X-Slack-Request-Timestamp']
    slack_signature = event['headers']['X-Slack-Signature']

    sig_basestring = f"v0:{timestamp}:{body}".encode('utf-8')
    my_signature = f"v0={hmac.new(os.environ['SLACK_KEY'].encode('utf-8'), sig_basestring, hashlib.sha256).hexdigest()}"
    return hmac.compare_digest(my_signature, slack_signature)


def respond(err, res=None):
    res["response_type"] = "in_channel"
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
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


def get_house_points(house):
    scan_success, scanned_wizards = scan_info(house)

    if scan_success:
        total_points = int(sum([wizard['points'] for wizard in scanned_wizards]))
        house_members = {}
        for wizard in scanned_wizards:
            if 'title' in wizard:
                house_members[wizard['title']] = wizard['points']
            else:
                house_members[wizard['username']] = wizard['points']

        members_by_points = {member: house_members[member] for member in sorted(house_members, key=house_members.get, reverse=True)}

        house_members_leaderboard = ""
        for member, points in members_by_points.items():
            house_members_leaderboard += f'_{member}_: {points}\n'
        message = {'text': f'_*{house.capitalize()}*_ has *{total_points}* points', 'attachments': [{"text": house_members_leaderboard}]}
    else:
        message = {'text': f'Something went wrong when getting the house points'}
    return message


def format_points(house_points):
    order_by_points = {house: house_points[house] for house in sorted(house_points, key=house_points.get, reverse=True)}
    houses_leaderboard = ""
    for prefix, (house, points) in zip(PREFIXES, order_by_points.items()):
        houses_leaderboard += f'_{prefix}*{house.capitalize()}* with *{points}* points_\n'
    return houses_leaderboard


def get_house_leaderboard():
    house_points = {}
    for house in HOGWARTS_HOUSES:
        scan_success, scanned_wizards = scan_info(house)
        house_points[house] = int(sum([wizard['points'] for wizard in scanned_wizards]))
    return format_points(house_points)


def parse_potential_house(house):
    target_house = house.lower()
    if target_house in HOGWARTS_HOUSES:
        return target_house
    else:
        return None


def create_wizard(wizard, house):
    wizard_found, wizard_info = get_item(wizard)
    wizard = remove_at(wizard)
    if not wizard_found:
        put_item(wizard, house)
        message = {'text': f'Welcome _*{wizard}*_ to _*{house}*_'}  # change username to full name eventually
    else:
        message = {'text': f'Wizard _*{wizard}*_ already exists'}
    return message


def display_instructions():
    instructions = {
        '- set house': '/dumbledore set house house_name _*or*_ /dumbledore set house :sorting-hat:\n',
        '- set title': '/dumbledore set title your name and whatever you wanna be called like Hogwarts Caretaker, be creative\n',
        '- leaderboard': '/dumbledore leaderboard\n',
        '- house leaderboard': '/dumbledore house_name\n',
        '- give points': '/dumbledore give 10 points to @wizard _*or*_ /dumbledore +10 @wizard\n',
        '- remove points': '/dumbledore remove 10 points from @wizard _*or*_ /dumbledore -10 @wizard\n',
        'HINT': f'\n House names are  _*{", ".join(HOGWARTS_HOUSES)}*_,  but if you are not sure which house do you'
                f' belong to, you can set it to :sorting-hat: and that will do the job'
    }

    dumbledore_orders = ""
    for order, command in instructions.items():
        dumbledore_orders += f'*{order}*: {command}'
    return dumbledore_orders


def clean_points(points):
    return max(-2000, points) if points < 0 else min(2000, points)


def get_wizard_points(wizard):
    wizard_found, wizard_info = get_item(wizard)
    if wizard_found:
        points = wizard_info['points']
        house = wizard_info['house'].capitalize()
        wizard_name = wizard['title'] if 'title' in wizard else wizard
        return {'text': f'_*{wizard_name}*_ has *{points}* points contributing to _{house}_'}
    else:
        return wizard_info


def allocate_points(wizard, points, assigner):
    points = clean_points(points)
    wizard_found, wizard_info = get_item(wizard)
    points_action = f'awarded *{points}* points to *{wizard}*' if points > 0 else f'removed *{points}* points from {wizard}'

    if wizard_found:
        update_points = update_item(
            wizard,
            expression_attributes={':p': points},
            update_expression='set points = points +:p',
            return_values="ALL_NEW"
         )

        update_to_zero = update_item(
            wizard,
            expression_attributes={':min': 0},
            condition_expression='points < :min',
            update_expression='set points = :min',
            return_values="UPDATED_NEW"
        )

        message = update_to_zero if update_to_zero else update_points
        total_points = message['Attributes']['points']
        message = {'text': f'_*{assigner}* has {points_action}, new total is *{total_points}* points_'}
        return message
    else:
        return wizard_info


def process_point_allocation(assigner, text):
    wizards, points = parse_slack_message(text)
    agg_messages = []
    if wizards:
        for wizard in wizards:
            # Avoid wizards from granting points to themselves
            if wizard == assigner and assigner not in HEADMASTER:
                message = get_wizard_points(wizard)
                message['attachments'] = [{'text': '_Are you awarding points to yourself? '
                                                   'That is like the *Forbidden Forest*: off limits_ :shame:'}]
            else:
                agg_messages.append(allocate_points(wizard, points, assigner))

        if agg_messages:
            message = {'text': '\n'.join(m_points['text'] for m_points in agg_messages)}
    else:
        message = {'text': f'_What do you think this is? Magic? '
                           f'I do not know which wizard do you want to give points to_'}
    return message


def set_hogwarts_house(text, assigner):
    hogwarts_house = None
    if len(text) == 3:
        if text[2] == ':sorting-hat:':
            hogwarts_house = random.choice(HOGWARTS_HOUSES)
        else:
            hogwarts_house = parse_potential_house(text[2])

    if hogwarts_house is not None:
        message = create_wizard(assigner, hogwarts_house)
    elif len(text) == 2:
        message = {'text': f'_What do you think this is? Magic? I do not know which house do you want to be in_'}
    else:
        message = {'text': f'_Are you a *muggle* or what? Spell the house name correctly:'
                           f' *{", ".join(HOGWARTS_HOUSES)}* or :sorting-hat:'}
    # ToDo: Add validation for when user type "set house" but it already belongs to a house, message displays that doesn't know which house to put him in
    return message


def set_wizards_title(text, wizard):
    title = ' '.join(text[2:])
    update_item(
        wizard,
        expression_attributes={':t': title},
        update_expression='set title = :t',
        return_values="UPDATED_NEW"
    )
    return {'text': f'_Your title has been updated to *{title}*_'}


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

def lambda_handler(event, context):
    message = {}
    #if not verify_request(event):
    #    return respond(None,  {"text":"Message verification failed"})

    params = parse_qs(event['body'])
    if 'text' in params:
        text = params['text'][0].replace('\xa0', ' ').split(" ")
        assigner = params['user_name'][0]
        point_allocators = ['give', 'remove', '+', '-']
        matching = [word for word in text if any(s in word for s in point_allocators)]

        # Display leaderboard for all houses
        if 'leaderboard' in text:
            house_points = get_house_leaderboard()
            message = {'text': f'{house_points}'}

        # Display leaderboard for the house requested
        elif len(text) == 1 and text[0].lower() in HOGWARTS_HOUSES:
            message = get_house_points(text[0].lower())

        # Set wizard to requested house
        elif ['set', 'house'] == text[0:2]:
            message = set_hogwarts_house(text, assigner)

        elif ['set', 'title'] == text[0:2] and len(text) > 2:
            message = set_wizards_title(text, assigner)

        # Allocate points
        elif matching:
            message = process_point_allocation(assigner, text)

        else:
            message = send_random_quote(assigner)

    else:
        instructions = display_instructions()
        message = {'text': f'First add yourself to your favorite house :european_castle:,  '
                           f'then you can start giving or taking points right away '
                           f':male_mage::skin-tone-2:  :deathly-hallows: ', 'attachments': [{"text": instructions}]}

    message["response_type"] = "in_channel"

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }



