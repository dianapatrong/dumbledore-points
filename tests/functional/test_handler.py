import json
import pytest
import boto3
from src import app


def get_slack_command(username, app_name, text):
    return {"body": f"user_name={username}&command=%2F{app_name}&text={text}"}


def test_display_instructions_handler():
    event = get_slack_command('dumbledore', 'dumbledore', '')
    ret = app.lambda_handler(event, "")
    data = json.loads(ret['body'])
    assert ret["statusCode"] == 200
    assert 'text' in ret['body']
    assert data['text'] == 'First add yourself to your favorite house :european_castle:,  then you can start ' \
                           'giving or taking points right away :male_mage::skin-tone-2:  :deathly-hallows: '


def test_set_house_no_text_found_handler():
    event = get_slack_command('dumbledore', 'dumbledore', 'set+house')
    ret = app.lambda_handler(event, "")
    data = json.loads(ret['body'])
    assert ret["statusCode"] == 200
    assert 'text' in ret['body']
    assert data['text'] == '_Are you a *muggle* or what? Spell the house name correctly: *gryffindor, ' \
                           'slytherin, ravenclaw, hufflepuff* or :sorting-hat:_'


def test_display_house_leaderboard_handler():
    event = get_slack_command('dumbledore', 'dumbledore', 'leaderboard')
    ret = app.lambda_handler(event, "")
    data = json.loads(ret['body'])
    assert ret["statusCode"] == 200
    assert 'text' in ret['body']
    assert data['text'] == '_Wizard *dumbledore* does not have priviledges yet, please enroll_'



"""
@pytest.fixture(scope='function')
def setup_table_item(use_moto):
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    item = {
        'PK': 'CUSTOMER#1',
        'SK': 'SURVEY#1',
        'customer_id': '1',
        'survey_id': '1',
        'survey_data': {'some': 'data'}
    }
    table.put_item(Item=item)
"""