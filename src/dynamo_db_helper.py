import boto3

dynamo = boto3.resource('dynamodb')
HOGWARTS_ALUMNI_TABLE = dynamo.Table('Hogwarts_Alumni')


def update_item(wizard, update_expression=None, condition_expression='', expression_attributes=None, return_values=None):
    if not condition_expression:
        try:
            db_response_2 = HOGWARTS_ALUMNI_TABLE.update_item(
                Key={
                    'username': wizard
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attributes,
                ReturnValues=return_values
            )
            return db_response_2
        except Exception as e:
            print("Allocate points Exception", e)
            return False
    else:
        try:
            db_response_2 = HOGWARTS_ALUMNI_TABLE.update_item(
                Key={
                    'username': wizard
                },
                UpdateExpression=update_expression,
                ConditionExpression=condition_expression,
                ExpressionAttributeValues=expression_attributes,
                ReturnValues=return_values
            )
            return db_response_2
        except Exception as e:
            print("Allocate points Exception", e)
            return False


def get_item(wizard):
    try:
        db_response = HOGWARTS_ALUMNI_TABLE.get_item(
            Key={
                'username': wizard
            }
        )
        item = db_response['Item']
        return True, item
    except Exception:
        message = {'text': f'Witch/wizard _*{wizard}*_ is not listed as a *Hogwarts Alumni*, most likely to be enrolled in _Beauxbatons_ or _Durmstrang_ '}
        return False, message


def scan_info(house):
    try:
        db_response = HOGWARTS_ALUMNI_TABLE.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('house').eq(house.lower())
        )
        items = db_response['Items']
        return True, items
    except Exception as e:
        return False, False


def put_item(wizard, house):
    HOGWARTS_ALUMNI_TABLE.put_item(
        Item={
            'username': wizard,
            'house': house,
            'points': 0
        }
    )
