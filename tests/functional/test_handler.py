import os
import json
import boto3
from src import app
import pytest
import hmac
import hashlib
from moto import mock_dynamodb2


@mock_dynamodb2
class TestDumbledorePoints:
    @staticmethod
    def apigw_event():
        """ Generates API GW Event"""
        with open("events/event.json") as json_file:
            return json.load(json_file)

    @staticmethod
    def get_slack_command(username, app_name, text):
        event = TestDumbledorePoints.apigw_event()
        event["body"] = f"user_name={username}&channel_id=testing&command=%2F{app_name}&text={text}"
        signature = f"v0:{event['headers']['X-Slack-Request-Timestamp']}:{event['body']}".encode('utf-8')
        my_signature = f"v0={hmac.new(os.environ['SLACK_KEY'].encode('utf-8'), signature, hashlib.sha256).hexdigest()}"
        event['headers']['X-Slack-Signature'] = my_signature
        return event

    def test_display_instructions_handler(self):
        event = TestDumbledorePoints.get_slack_command('dumbledore', 'dumbledore', '')
        print("EVENT ", event)
        ret = app.lambda_handler(event, "")
        data = json.loads(ret['body'])
        assert ret["statusCode"] == 200
        assert 'text' in ret['body']
        assert data['text'] == 'First add yourself to your favorite house :european_castle:,  then you can start ' \
                               'giving or taking points right away :male_mage::skin-tone-2:  :deathly-hallows: '

    def test_set_house_no_text_found_handler(self):
        event = TestDumbledorePoints.get_slack_command('dumbledore', 'dumbledore', 'set+house')
        ret = app.lambda_handler(event, "")
        data = json.loads(ret['body'])
        assert ret["statusCode"] == 200
        assert 'text' in ret['body']
        assert data['text'] == '_Are you a *muggle* or what? Spell the house name correctly: *gryffindor, ' \
                               'slytherin, ravenclaw, hufflepuff* or :sorting-hat:_'

    def test_display_house_leaderboard_handler_user_not_exists(self):
        event = TestDumbledorePoints.get_slack_command('dumbledore', 'dumbledore', 'leaderboard')
        ret = app.lambda_handler(event, "")
        data = json.loads(ret['body'])
        assert ret["statusCode"] == 200
        assert 'text' in ret['body']
        assert data['text'] == '_Wizard *dumbledore* does not have priviledges yet, please enroll_'

    def test_display_house_leaderboard_handler_user_exists(self, use_moto):
        use_moto()
        event = TestDumbledorePoints.get_slack_command('dumbledore', 'dumbledore', 'gryffindor')
        TestDumbledorePoints.load_items_into_mock_db()
        ret = app.lambda_handler(event, "")
        data = json.loads(ret['body'])
        assert ret["statusCode"] == 200
        assert 'text' in ret['body']
        assert data['text'] == '_*gryffindor* has *20* points_'
        assert 'attachments' in ret['body']
        assert data['attachments'] == [{'text': '_dumbledore_: 20\n'}]

    @staticmethod
    def load_items_into_mock_db():
        table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
        item = {'username': 'dumbledore', 'house': 'gryffindor', 'points': 20}
        table.put_item(Item=item)
