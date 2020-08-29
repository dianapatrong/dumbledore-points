import json
import pytest
import os


@pytest.fixture()
def apigw_event():
    with open("events/event.json") as json_file:
        return json.load(json_file)


def test_lambda_handler(apigw_event, mocker):
    from src import app
    ret = app.lambda_handler(apigw_event, "")
    data = json.loads(ret["body"])


    assert ret["statusCode"] == 200
    assert 'text' in ret['body']
    assert data['text'] == "First add yourself to your favorite house :european_castle:,  then you can start giving or taking points right away :male_mage::skin-tone-2:  :deathly-hallows: "
    # assert "location" in data.dict_keys()
