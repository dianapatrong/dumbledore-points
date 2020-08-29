import json
import pytest
import os
import unittest
from src import app


class TestDumbledorePoints(unittest.TestCase):

    def setUp(self) -> None:
        pass

    @staticmethod
    def load_event(filename):
        with open(f'events/{filename}.json') as json_file:
            return json.load(json_file)

    def test_display_instructions(self):
        ret = app.lambda_handler(self.load_event('instructions'), "")
        data = json.loads(ret['body'])
        assert ret["statusCode"] == 200
        assert 'text' in ret['body']
        assert data['text'] == 'First add yourself to your favorite house :european_castle:,  then you can start ' \
                               'giving or taking points right away :male_mage::skin-tone-2:  :deathly-hallows: '

    @pytest.mark.parametrize('command',[('set_house'), ('set_house_gryffindor')])
    def test_set_house(self, command):
        ret = app.lambda_handler(self.load_event(command), "")
        data = json.loads(ret[command]["body"])
        assert ret["statusCode"] == 200
        assert 'text' in ret['body']
        assert data['text'] == '_What do you think this is? Magic? I do not know which house do you want to be in_'


    def tearDown(self) -> None:
        pass