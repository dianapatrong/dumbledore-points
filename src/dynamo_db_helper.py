from boto3.dynamodb.conditions import Key, Attr


def update_item(table, wizard, update_expression=None, attributes=None, return_values=None):
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


def get_item_info(table, wizard):
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


def get_item_exists(table, wizard):
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


def scan_info(table, house):
    try:
        db_response = table.scan(
            FilterExpression=Attr('house').eq(house.lower())
        )
        items = db_response['Items']
        return items
    except Exception as e:
        print("Something went wrong: ", e)
        return False


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
        print("Something went wrong: ", e)
