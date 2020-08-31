from boto3.dynamodb.conditions import Key, Attr
from typing import Union, Dict, Any
from mypy_boto3_dynamodb.service_resource import Table


def update_item(table: Table, wizard: str, update_expression: str, attributes: dict, return_values: Any) -> Union[Any, bool]:
    try:
        db_response = table.update_item(
            Key={
                'username': wizard
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=attributes,
            ReturnValues=return_values
        )
        return db_response
    except Exception as e:
        print("Something went wrong: ", e)
        return False


def get_item_info(table: Table, wizard: str) -> Dict[Any, Any]:
    try:
        db_response = table.get_item(
            Key={
                'username': wizard
            }
        )
        item = db_response['Item']
        return item
    except Exception as e:
        print("Something went wrong: ", e)
        message = {'text': f'Witch/wizard _*{wizard}*_ is not listed as a *Hogwarts Alumni*, most likely to be enrolled in _Beauxbatons_ or _Durmstrang_'}
        return message


def get_item_exists(table: Table, wizard: str) -> bool:
    try:
        db_response = table.get_item(
            Key={
                'username': wizard
            }
        )
        item = db_response['Item']
        return True
    except Exception as e:
        print("Something went wrong: ", e)
        return False


def scan_info(table: Table, house: str) -> Union[Any, bool]:
    try:
        db_response = table.scan(
            FilterExpression=Attr('house').eq(house.lower())
        )
        items = db_response['Items']
        return items
    except Exception as e:
        print("Something went wrong: ", e)
        return False


def put_item(table: Table, wizard: str, house: str) -> None:
    try:
        table.put_item(
            Item={
                'username': wizard,
                'house': house,
                'points': 0
            }
        )
    except Exception as e:
        print("Something went wrong: ", e)
