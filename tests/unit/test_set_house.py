import boto3
from moto import mock_dynamodb2


def test_parse_house_text_valid():
    from src.app import parse_house_text
    house = parse_house_text(['gryffindor'])
    assert house == 'gryffindor'


def test_parse_house_text_invalid():
    from src.app import parse_house_text
    house = parse_house_text(['dubadubadubadu'])
    assert house == None


@mock_dynamodb2
def test_create_wizard(use_moto):
    from src.app import create_wizard
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    message = create_wizard(table, 'dracomalfoy', 'slytherin')
    assert message == {'text': 'Welcome _*dracomalfoy*_ to _*slytherin*_'}


@mock_dynamodb2
def test_create_already_existent_wizard(use_moto):
    from src.app import create_wizard
    use_moto()
    item = {
        'username': 'dracomalfoy',
        'house': 'gryffindor',
        'points': 1
    }
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    table.put_item(Item=item)
    message = create_wizard(table, 'dracomalfoy', 'slytherin')
    assert message == {'text': 'Wizard _*dracomalfoy*_ already exists'}


def test_remove_at():
    from src.app import remove_at
    assert remove_at('@hermionegranger') == 'hermionegranger'

