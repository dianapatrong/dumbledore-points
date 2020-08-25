import json
import urllib
import time
import os
import hmac
import hashlib
import boto3
from urllib.parse import parse_qs

dynamo = boto3.resource('dynamodb')




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


def parse_message(text):
    users = list(filter(lambda x: x.startswith('@'), text))
    users = list(set(users))
    return users


def lambda_handler(event, context):
    headers = event['headers']
    body = event['body']

    # if not verify_request(event):
    #    return respond(None,  {"text":"Message verification failed"})

    table = dynamo.Table('HouseMembers')
    params = parse_qs(event['body'])

    if 'text' in params:
        text = params['text'][0].split(" ")
        assigner = params['user_name'][0]
        users, points, msg = parse_message(text)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda, ')
    }



