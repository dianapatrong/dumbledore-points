import json
import urllib
import time
import os
import hmac
import hashlib
import boto3
from urllib.parse import parse_qs
import requests

dynamo = boto3.resource('dynamodb')
HOGWARTS_ALUMNI_TABLE = dynamo.Table('Hogwarts_Alumni')

HEADMASTER = ['vahev']
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


def parse_slack_message(text):
    give_points = True if [word for word in text if any(s in word for s in ['give', '+'])] else False
    wizards = [remove_at(name) for name in text if name.startswith('@')]
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

    print("give_points ", give_points)
    print("possible_points", possible_points)
    print("points ", points)

    return wizards, points


def get_house_points(house):
    """Iterates over the HOUSES and save their points into a dictionary"""
    try:
        db_response = HOGWARTS_ALUMNI_TABLE.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('house').eq(house)
        )
        items = db_response['Items']
        total_points = int(sum([i['points'] for i in items]))
        house_members = {}
        for i in items:
            house_members[i['username']] = i['points']
        members_by_points = {member: house_members[member] for member in sorted(house_members, key=house_members.get, reverse=True)}
        house_members_leaderboard = ""
        for member, points in members_by_points.items():
            house_members_leaderboard += f'_{member}_: {points}\n'
        message = {'text': f'_*{house.capitalize()}*_ has *{total_points}* points', 'attachments': [{"text": house_members_leaderboard}]}
        return message
    except Exception as e:
        return {'text': f'Something went wrong when getting the house points: {e}'}


def format_points(house_points):
    order_by_points = {house: house_points[house] for house in sorted(house_points, key=house_points.get, reverse=True)}
    houses_leaderboard = ""
    for prefix, (house, points) in zip(PREFIXES, order_by_points.items()):
        houses_leaderboard += f'_{prefix}*{house.capitalize()}* with *{points}* points_\n'
    return houses_leaderboard


def get_house_leaderboard():
    house_points = {}
    for house in HOGWARTS_HOUSES:
        try:
            db_response = HOGWARTS_ALUMNI_TABLE.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('house').eq(house.lower()))
            items = db_response['Items']
            house_points[house] = int(sum([i['points'] for i in items]))
        except Exception as e:
            return e
    return format_points(house_points)


def parse_potential_house(house):
    target_house = house.lower()
    if target_house in HOGWARTS_HOUSES:
        return target_house
    else:
        return None


def create_wizard(wizard, house):
    wizard_found = check_user_permission(wizard)
    wizard = remove_at(wizard)
    if not wizard_found:
        HOGWARTS_ALUMNI_TABLE.put_item(
            Item={
                'username': wizard,
                'house': house,
                'points': 0
            }
        )
        message = {'text': f'Welcome _*{wizard}*_ to _*{house}*_'}  # change username to full name eventually
    else:
        message = {'text': f'Wizard _*{wizard}*_ already exists'}
    return message


def check_user_permission(wizard):
    try:
        db_response = HOGWARTS_ALUMNI_TABLE.get_item(
            Key={
                'username': wizard
            }
        )
        item = db_response['Item']
        return True
    except Exception as e:
        print("check_user_permission Exception:", e)
        return False


def display_instructions():
    instructions = {
        '- set house': '/dumbledore set house <house>\n',
        '- leaderboard': '/dumbledore leaderboard\n',
        '- house leaderboard': '/dumbledore <house>\n',
        '- give points': '/dumbledore give 10 points to @wizard _*or*_ /dumbledore +10 @wizard\n',
        '- remove points': '/dumbledore remove 10 points from @wizard _*or*_ /dumbledore -10 @wizard\n',
        'HINT': f'\n House names are  _*{", ".join(HOGWARTS_HOUSES)}*_,  but if you are not sure which house do you'
                f' belong to, you can set it to random and that will do the job'
    }

    dumbledore_orders = ""
    for order, command in instructions.items():
        dumbledore_orders += f'*{order}*: {command}'
    return dumbledore_orders


def get_wizard_points(wizard):
    try:
        db_response = HOGWARTS_ALUMNI_TABLE.get_item(
            Key={
                'username': wizard
            }
        )
        item = db_response['Item']
        points = item['points']
        house = item['house'].capitalize()
        return {'text': f'_*{wizard}*_ has *{points}* points contributing to _{house}_'}
    except Exception:
        return {'text': f'Witch/wizard _*{wizard}*_ is not listed as a *Hogwarts Alumni*, most likely to be enrolled in _Beauxbatons_ or _Durmstrang_ '}


def clean_points(points):
    return max(-2000, points) if points < 0 else min(2000, points)


def allocate_points(wizard, points, assigner):
    try:
        db_response_1 = HOGWARTS_ALUMNI_TABLE.get_item(
            Key={
                'username': wizard
            }
        )
    except Exception as e:
        print("allocate_points 1 Exception:", e)

    points = clean_points(points)
    print("clean points", points)
    wizard_found = check_user_permission(wizard)
    points_action = f'awarded _*{points}*_ points to {wizard}' if points > 0 else f'removed _*{points}*_ points from {wizard}'

    if wizard_found:
        try:
            db_response_2 = HOGWARTS_ALUMNI_TABLE.update_item(
                Key={
                    'username': wizard
                },
                UpdateExpression='set points = points +:p',
                ExpressionAttributeValues={
                    ':p': points
                },
                ReturnValues="ALL_NEW"
            )
        except Exception as e:
            print("Allocate points Exception", e)

        try:
            db_response_3 = HOGWARTS_ALUMNI_TABLE.update_item(
                Key={
                    'username': wizard
                },
                UpdateExpression="set points = :min",
                ConditionExpression="points < :min",
                ExpressionAttributeValues={
                    ':min': 0
                },
                ReturnValues="UPDATED_NEW"
            )
            message = db_response_3
        except Exception as e:
            message = db_response_2

        total_points = message['Attributes']['points']
        message = {'text': f'{assigner} has {points_action}, new total is _*{total_points}*_ points'}
        return message


def lambda_handler(event, context):
    message = {}
    headers = event['headers']
    body = event['body']

    #if not verify_request(event):
    #    return respond(None,  {"text":"Message verification failed"})

    params = parse_qs(event['body'])
    if 'text' in params:
        text = params['text'][0].replace('\xa0', ' ').split(" ")
        assigner = params['user_name'][0]

        # Display leaderboard for all houses
        if 'leaderboard' in text:
            house_points = get_house_leaderboard()
            message = {'text': f'{house_points}'}

        # Display leaderboard for the house requested
        if len(text) == 1 and text[0].lower() in HOGWARTS_HOUSES:
            message = get_house_points(text[0].lower())

        # Set wizard to requested house
        hogwarts_house = None
        if ['set', 'house'] == text[0:2]:
            if len(text) == 3:
                if text[2] == 'random':
                    sorting_hat = requests.get('https://www.potterapi.com/v1/sortingHat')
                    hogwarts_house = sorting_hat.text.replace('"', '').lower()
                else:
                    hogwarts_house = parse_potential_house(text[2])

            if hogwarts_house is not None:
                message = create_wizard(assigner, hogwarts_house)
            elif len(text) == 2:
                message = {'text': f'_What do you think this is? Magic? I do not know which house do you want to be in_'}
            else:
                message = {'text': f'_Are you a *muggle* or what? Spell the house name correctly:'
                                   f' *{", ".join(HOGWARTS_HOUSES)}* or *random*_'}
            print("Len(texT)", len(text))
            print("MESSAGE", message)

        # Allocate points
        point_allocators = ['give', 'remove', '+', '-']
        matching = [word for word in text if any(s in word for s in point_allocators)]
        print("matching", matching)
        if matching:
            print("allocate points text ", text)
            wizards, points = parse_slack_message(text)
            agg_messages = []
            for wizard in wizards:
                # Avoid wizards from granting points to themselves
                if wizard == assigner and assigner not in HEADMASTER:
                    message = get_wizard_points(wizard)
                    message['attachments'] = [{'text': '_Are you awarding points to yourself? That is like the *Forbidden Forest*: off limits_ :shame:'}]
                else:
                    agg_messages.append(allocate_points(wizard, points, assigner))

            if agg_messages:
                message = {'text': '\n'.join(m_points['text'] for m_points in agg_messages)}
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



