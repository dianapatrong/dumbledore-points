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
HOGWARTS_HOUSES = ['GRYFFINDOR', 'SLYTHERIN', 'RAVENCLAW', 'HUFFLEPUFF']


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
        total_points = sum([i['points'] for i in items])
        house_members = {}

        return "YAY"
    except Exception as e:
        return {'text': 'Something went wrong when getting the house points'}


def parse_potential_house(house):
    target_house = house.lower()
    if target_house in HOGWARTS_HOUSES:
        return target_house
    else:
        return "THAT IS NOT A HOUSE "


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
        HOGWARTS_ALUMNI_TABLE.get_item(
            Key={
                'username': wizard
            }
        )
        return True
    except Exception as e:
        print(e)
        return False


def get_house_leaderboard():
    house_points = {}
    for house in HOGWARTS_HOUSES:
        try:
            db_response = HOGWARTS_ALUMNI_TABLE.scan(FilterExpression=boto3.dynamodb.conditions.Attr('house').eq(house))
            items = db_response['Items']
            house_points[house] = sum([i['points'] for i in items])
            return house_points
        except Exception as e:
            return "ERROR"


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

        if len(text) == 1:
            if text[0].upper() in HOGWARTS_HOUSES:
                message = get_house_points(text[0].lower())

        if len(text) > 1:
            # users  set house
            if text[0:2] == ['set', 'house']:
                # Text : /dumbledore set house @house
                hogwarts_house = parse_potential_house(text[2])
                ## RESPOND WITH ERROR IF POTENTIAL HOUSE NOT IN
                message = create_wizard(assigner, hogwarts_house)

            users, points = parse_slack_message(text)
    else:
        house_points = get_house_leaderboard()
        message = {'text': f'{house_points}'}

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }



