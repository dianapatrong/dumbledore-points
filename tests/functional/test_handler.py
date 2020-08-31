import json
import pytest
from src import app


def load_event(filename):
    with open(f'events/{filename}.json') as json_file:
        return json.load(json_file)


def test_display_instructions():
    ret = app.lambda_handler(load_event('instructions'), "")
    data = json.loads(ret['body'])
    assert ret["statusCode"] == 200
    assert 'text' in ret['body']
    assert data['text'] == 'First add yourself to your favorite house :european_castle:,  then you can start ' \
                           'giving or taking points right away :male_mage::skin-tone-2:  :deathly-hallows: '

