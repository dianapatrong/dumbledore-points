import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
def test_process_point_allocation_existent_user(use_moto):
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
    print(message)
    assert message == {'text': '_*bellatrix* has awarded *10* points to *dobby*, new total is *12* points_'}


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
def test_parse_slack_message(use_moto):
    from src.app import parse_slack_message
    pass