import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
def test_process_point_allocation_give(use_moto):
    from src.app import process_point_allocation
    use_moto()
    items = [
        {'username': 'dobby', 'house': 'slytherin', 'points': 2},
        {'username': 'bellatrix', 'house': 'slytherin', 'points': 11}
    ]
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    with table.batch_writer() as batch:
        for i in items:
            batch.put_item(Item=i)
    message = process_point_allocation(table, ['dobby'], 10, 'bellatrix')
    assert message == {'text': '_*bellatrix* has awarded *10* points to *dobby*, new total is *12* points_'}


@mock_dynamodb2
def test_process_point_allocation_remove(use_moto):
    from src.app import process_point_allocation
    use_moto()
    items = [
        {'username': 'dobby', 'house': 'slytherin', 'points': 10},
        {'username': 'bellatrix', 'house': 'slytherin', 'points': 20}
    ]
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    with table.batch_writer() as batch:
        for i in items:
            batch.put_item(Item=i)
    message = process_point_allocation(table, ['dobby'], -10, 'bellatrix')
    assert message == {'text': '_*bellatrix* has removed *-10* points from *dobby*, new total is *0* points_'}


@mock_dynamodb2
def test_process_point_allocation_headmaster(use_moto):
    from src.app import process_point_allocation
    use_moto()
    items = [
        {'username': 'dumbledore', 'house': 'gryffindor', 'points': 10},
    ]
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    with table.batch_writer() as batch:
        for i in items:
            batch.put_item(Item=i)
    message = process_point_allocation(table, ['dumbledore'], 10, 'dumbledore')
    assert message == {'text': '_*dumbledore* has awarded *10* points to *dumbledore*, new total is *20* points_'}


@mock_dynamodb2
def test_process_point_allocation_cheater(use_moto):
    from src.app import process_point_allocation
    use_moto()
    items = [
        {'username': 'gilderoylockheart', 'house': 'gryffindor', 'points': 10},
    ]
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    with table.batch_writer() as batch:
        for i in items:
            batch.put_item(Item=i)
    message = process_point_allocation(table, ['gilderoylockheart'], 10, 'gilderoylockheart')
    assert message == {'attachments': [{'text': '_Are you awarding points to yourself? That is like the '
                                                '*Forbidden Forest*: off limits_ :shame:'}],
                                       'text': '_*gilderoylockheart*_ has *10* points, cheater'}


@mock_dynamodb2
def test_get_wizard_points(use_moto):
    from src.app import get_wizard_points
    use_moto()
    item = {'username': 'ginnyweasley','house': 'gryffindor','points': 50}
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    table.put_item(Item=item)
    points = get_wizard_points(table, 'ginnyweasley')
    assert points == 50


@mock_dynamodb2
def test_allocate_points_found_wizards(use_moto):
    from src.app import allocate_points
    use_moto()
    items = [
        {'username': 'dumbledore', 'house': 'gryffindor', 'points': 2},
        {'username': 'hagrid', 'house': 'gryffindor', 'points': 11}
    ]
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    with table.batch_writer() as batch:
        for i in items:
            batch.put_item(Item=i)
    message = allocate_points(table, 'dumbledore', 12, 'hagrid')
    assert message == {'text': '_*hagrid* has awarded *12* points to *dumbledore*, new total is *14* points_'}


@mock_dynamodb2
def test_parse_slack_message_single_user(use_moto):
    from src.app import parse_points_message
    wizards, points = parse_points_message(['give', '10', '@dumbledore'])
    assert wizards == ['dumbledore']
    assert points == 10


@mock_dynamodb2
def test_parse_slack_message_multiple_users(use_moto):
    from src.app import parse_points_message
    wizards, points = parse_points_message(['give', '10', '@dumbledore', '@harrypotter'])
    assert wizards == ['dumbledore', 'harrypotter']
    assert points == 10


@mock_dynamodb2
def test_parse_slack_message_multiple_points(use_moto):
    from src.app import parse_points_message
    wizards, points = parse_points_message(['give', '10', '@dumbledore', '59'])
    assert wizards == ['dumbledore']
    assert points == 10


@mock_dynamodb2
def test_parse_slack_message_no_users(use_moto):
    from src.app import parse_points_message
    wizards, points = parse_points_message(['give', '10'])
    assert wizards == False
    assert points == False


@mock_dynamodb2
def test_parse_slack_message_no_points(use_moto):
    from src.app import parse_points_message
    wizards, points = parse_points_message(['give', '@harrypotter'])
    assert wizards == ['harrypotter']
    assert points == 200  # Default number of points


def test_parse_give_points():
    from src.app import parse_points
    points = parse_points(['give', '20', '39', '@harrypotter'], True)
    assert points == 20


def test_parse_give_points_plus():
    from src.app import parse_points
    points = parse_points(['+', '20', '39', '@harrypotter'], True)
    assert points == 20


def test_parse_remove_points():
    from src.app import parse_points
    points = parse_points(['remove', '20', '39', '@harrypotter'], False)
    assert points == -20


def test_parse_remove_points_less():
    from src.app import parse_points
    points = parse_points(['-', '20', '39', '@harrypotter'], False)
    assert points == -20


def test_clean_points_negative_over():
    from src.app import clean_points
    points = clean_points(-9999)
    assert points == -2000


def test_clean_points_positive_over():
    from src.app import clean_points
    points = clean_points(9999)
    assert points == 2000


def test_clean_points_positive():
    from src.app import clean_points
    points = clean_points(300)
    assert points == 300


def test_clean_points_negative():
    from src.app import clean_points
    points = clean_points(-250)
    assert points == -250
