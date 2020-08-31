import json
import boto3
from src import app
import pytest
from moto import mock_dynamodb2


class TestDumbledorePoints():
    @staticmethod
    def get_slack_command(username, app_name, text):
        return {"body": f"user_name={username}&command=%2F{app_name}&text={text}"}

    def test_display_instructions_handler(self):
        event = TestDumbledorePoints.get_slack_command('dumbledore', 'dumbledore', '')
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

