import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
def test_create_wizard(use_moto):
    use_moto()
    from src.app import create_wizard
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    message = create_wizard(table, 'snape', 'slytherin')
    assert message == {'text': 'Welcome _*snape*_ to _*slytherin*_'}


@mock_dynamodb2
def test_hogwarts_leaderboard(use_moto):
    from src.app import get_house_leaderboard
    use_moto()
    table = boto3.resource('dynamodb', region_name='us-east-1').Table('alumni')
    house_points = get_house_leaderboard(table)
    assert house_points == {'gryffindor': 0, 'hufflepuff': 0, 'ravenclaw': 0, 'slytherin': 0}


def test_format_leaderboard_points(use_moto):
    from src.app import format_points
    use_moto()
    house_points = {'gryffindor': 0, 'hufflepuff': 0, 'ravenclaw': 0, 'slytherin': 0}
    assert format_points(house_points) == "_In the lead is *Gryffindor* with *0* points_\n" \
                                          "_Second place is *Hufflepuff* with *0* points_\n" \
                                          "_Third place is *Ravenclaw* with *0* points_\n" \
                                          "_Fourth place is *Slytherin* with *0* points_\n"




