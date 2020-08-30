import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
def test_set_hogwarts_house():

@mock_dynamodb2
def test_create_wizard(use_moto):
    use_moto()
    from src.app import create_wizard
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    message = create_wizard(table, 'snape', 'slytherin')
    assert message == {'text': 'Welcome _*snape*_ to _*slytherin*_'}
