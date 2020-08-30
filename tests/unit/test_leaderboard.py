import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
def test_hogwarts_leaderboard(use_moto):
    from src.app import get_house_leaderboard
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    house_points = get_house_leaderboard(table)
    assert house_points == {'gryffindor': 0, 'hufflepuff': 0, 'ravenclaw': 0, 'slytherin': 0}


def test_format_leaderboard_points():
    from src.app import format_points
    house_points = {'gryffindor': 0, 'hufflepuff': 0, 'ravenclaw': 0, 'slytherin': 0}
    assert format_points(house_points) == "_In the lead is *Gryffindor* with *0* points_\n" \
                                          "_Second place is *Hufflepuff* with *0* points_\n" \
                                          "_Third place is *Ravenclaw* with *0* points_\n" \
                                          "_Fourth place is *Slytherin* with *0* points_\n"


@mock_dynamodb2
def test_get_house_points(use_moto):
    from src.app import get_house_points
    use_moto()
    items = [
        {'username': 'dumbledore', 'house': 'gryffindor', 'points': 9999},
        {'username': 'harrypotter', 'house': 'gryffindor', 'points': 1}
    ]
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    with table.batch_writer() as batch:
        for i in items:
            batch.put_item(Item=i)
    total_points, house_points = get_house_points(table, 'gryffindor')
    assert house_points == '_dumbledore_: 9999\n_harrypotter_: 1\n'
    assert total_points == 10000
    """x = table.get_item(Key={'username': 'dumbledore'})
    print("DUMBLEDORE", x)

    #x = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('house').eq('gryffindor'.lower()))
    #print("HOUSES", x)"""


