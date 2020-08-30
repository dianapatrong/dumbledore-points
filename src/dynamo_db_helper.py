import boto3

from boto3.dynamodb.conditions import Key, Attr

def update_item(table, wizard, update_expression=None, condition='', attributes=None, return_values=None):
    try:
        db_response = table.update_item(
            Key={
                'username': wizard
            },
            UpdateExpression=update_expression,
            ConditionExpression=condition,
            ExpressionAttributeValues=attributes,
            ReturnValues=return_values
        )
        return db_response
    except Exception as e:
        print("Allocate points Exception", e)
        return False


def get_item(table, wizard):
    try:
        db_response = table.get_item(
            Key={
                'username': wizard
            }
        )
        item = db_response['Item']
        return True, item
    except Exception as e:
        print("GET ITEM EXCEPTION ", e)
        message = {'text': f'Witch/wizard _*{wizard}*_ is not listed as a *Hogwarts Alumni*, most likely to be enrolled in _Beauxbatons_ or _Durmstrang_'}
        return False, message


def scan_info(table, house):
    try:
        db_response = table.scan(
            FilterExpression=Attr('house').eq(house.lower())
        )
        items = db_response['Items']
        return True, items
    except Exception as e:
        print("ECEPTION", e)
        return False, False


def put_item(table, wizard, house):
    try:
        table.put_item(
            Item={
                'username': wizard,
                'house': house,
                'points': 0
            }
        )
    except Exception as e:
        print("EXCEPTION,", e)
