import os
import boto3
import pytest
from moto import mock_dynamodb2


@pytest.fixture
def use_moto():
    @mock_dynamodb2
    def dynamodb_client():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='alumni',
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            },
        )
        return dynamodb
    return dynamodb_client
