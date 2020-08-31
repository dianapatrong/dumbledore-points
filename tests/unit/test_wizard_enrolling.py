import boto3
from moto import mock_dynamodb2


def test_parse_house_text_valid():
    from src.app import parse_house_text
    house = parse_house_text(['gryffindor'])
    assert house == 'gryffindor'


def test_parse_house_text_invalid():
    from src.app import parse_house_text
    house = parse_house_text(['expelliarmus'])
    assert house == None


@mock_dynamodb2
def test_create_wizard(use_moto):
    from src.app import create_wizard
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    message = create_wizard(table, 'dracomalfoy', 'slytherin')
    assert message == {'text': 'Welcome _*dracomalfoy*_ to _*slytherin*_'}


def test_remove_at():
    from src.app import remove_at
    assert remove_at('@HermioneGranger') == 'hermionegranger'


@mock_dynamodb2
def test_set_wizard_title(use_moto):
    from src.app import set_wizards_title
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    item = {'username': 'ronweasley', 'house': 'gryffindor', 'points': 88}
    table.put_item(Item=item)
    title_message = set_wizards_title(table, 'Ron Weasley, Quidditch Captain', 'ronweasley' )
    assert title_message == {'text': '_Your title has been updated to *Ron Weasley, Quidditch Captain*_'}


@mock_dynamodb2
def test_set_wizard_title_null(use_moto):
    from src.app import set_wizards_title
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    item = {'username': 'ronweasley', 'house': 'gryffindor', 'points': 88}
    table.put_item(Item=item)
    title_message = set_wizards_title(table, '', 'ronweasley')
    assert title_message == {'text': '_Give the instructions another read, maybe it takes twice to understand_'}


@mock_dynamodb2
def test_get_wizard_existing_title(use_moto):
    from src.app import get_title_if_exists
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    item = {'username': 'ronweasley', 'house': 'gryffindor', 'points': 88, 'title': 'Ron Weasley, Quidditch Captain'}
    table.put_item(Item=item)
    title = get_title_if_exists(table, 'ronweasley')
    assert title == 'Ron Weasley, Quidditch Captain'


@mock_dynamodb2
def test_get_wizard_non_existing_title(use_moto):
    from src.app import get_title_if_exists
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    item = {'username': 'ronweasley', 'house': 'gryffindor', 'points': 88}
    table.put_item(Item=item)
    title = get_title_if_exists(table, 'ronweasley')
    assert title == 'ronweasley'


@mock_dynamodb2
def test_verify_not_registered_user(use_moto):
    from src.app import verify_user
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    exists = verify_user(table, 'voldemort')
    assert exists == False


@mock_dynamodb2
def test_verify_registered_user(use_moto):
    from src.app import verify_user
    use_moto()
    item = {'username': 'voldemort', 'house': 'gryffindor', 'points': 1}
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    table.put_item(Item=item)
    exists = verify_user(table, 'voldemort')
    assert exists == True


def test_parse_potential_house_bold_italic():
    from src.app import parse_potential_house
    house = parse_potential_house('_*slytherin*_')
    assert house == 'slytherin'
