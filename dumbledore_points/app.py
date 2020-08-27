import json
import urllib
import time
import os
import hmac
import hashlib
import boto3
from urllib.parse import parse_qs

dynamo = boto3.resource('dynamodb')
HOGWARTS_ALUMNI_TABLE = dynamo.Table('Hogwarts_Alumni')

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


def parse_slack_message(text):
    users = [remove_at(name) for name in text if name.startswith('@')]
    possible_points = [int(num) for num in text if num.isnumeric()]
    points = possible_points[0] if possible_points[0] > 0 else 200  # default number, maybe send an error message
    return users, points


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
        message = {'text': f'Welcome {wizard} to {house}'}  # change username to full name eventually
    else:
        message = {'text': f'Wizard {wizard} already exists'}
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
        print(e)
        return False


def display_instructions():
    # /dumbledore set house HOUSE_NAME
    # /dumbledore leaderboard
    instructions = {
        'set_house': 'Add yourself to a house: _/dumbledore set house $house_name_\n',
        'leaderboard': 'To display the leaderboard: _/dumbledore leaderboard_ \n',
        'house_leaderboard': 'To display the leaderboard of your house: _/dumbledore $house_name',
        'house_names': f'\n *HINT*: House names are  _*{", ".join(HOGWARTS_HOUSES)}*_'
    }

    dumbledore_orders = ""

    for order, command in instructions.items():
        dumbledore_orders += f'{command}'
    return dumbledore_orders


def lambda_handler(event, context):
    message = {}
    headers = event['headers']
    body = event['body']

    # if not verify_request(event):
    #    return respond(None,  {"text":"Message verification failed"})

    params = parse_qs(event['body'])

    if 'text' in params:
        text = params['text'][0].split(" ")
        assigner = params['user_name'][0]

        # Display leaderboard for all houses
        if 'leaderboard' in text:
            house_points = get_house_leaderboard()
            message = {'text': f'{house_points}'}

        # Display leaderboard for the house requested
        if len(text) == 1 and text[0].lower() in HOGWARTS_HOUSES:
            message = get_house_points(text[0].lower())

        if len(text) > 1:
            # users  set house
            if text[0:2] == ['set', 'house']:
                # Text : /dumbledore set house @house
                hogwarts_house = parse_potential_house(text[2])
                if hogwarts_house is not None:
                    message = create_wizard(assigner, hogwarts_house)
                else:
                    message = {
                        'text': f'Come on, Harry Potter was released June 26, 1997 you should know the house names by now: _*{", ".join(HOGWARTS_HOUSES)}*_'}

            # users, points = parse_slack_message(text)
    else:
        instructions = display_instructions()
        message = {'text': f'{instructions}'}

    message["response_type"] = "in_channel"

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }



