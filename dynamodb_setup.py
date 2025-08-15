#!/usr/bin/env python3
"""
Script to create DynamoDB table for TV Show Tracker
"""

import boto3
from botocore.exceptions import ClientError
import sys


def create_tv_show_table(table_name='tv_show_tracker'):
    """Create DynamoDB table for TV show tracking"""

    dynamodb = boto3.resource('dynamodb')

    try:
        # Create table
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'tv_show',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'tv_show',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing
        )

        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"Table {table_name} created successfully!")

        # Print table info
        print(f"Table ARN: {table.table_arn}")
        print(f"Table Status: {table.table_status}")

        return table

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists!")
            return dynamodb.Table(table_name)
        else:
            print(f"Error creating table: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def add_sample_data(table_name='tv_show_tracker'):
    """Add some sample data to the table"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    sample_data = [
        {
            'username': 'john_doe',
            'tv_show': 'Breaking Bad',
            'season': 3,
            'episode': 7,
            'last_updated': '2024-01-15T10:30:00Z'
        },
        {
            'username': 'john_doe',
            'tv_show': 'The Office',
            'season': 5,
            'episode': 12,
            'last_updated': '2024-01-14T20:15:00Z'
        },
        {
            'username': 'jane_smith',
            'tv_show': 'Stranger Things',
            'season': 4,
            'episode': 3,
            'last_updated': '2024-01-16T14:45:00Z'
        }
    ]

    try:
        for item in sample_data:
            table.put_item(Item=item)
            print(f"Added sample data: {item['username']} - {item['tv_show']}")

        print("Sample data added successfully!")

    except ClientError as e:
        print(f"Error adding sample data: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == '__main__':
    table_name = 'tv_show_tracker'

    if len(sys.argv) > 1:
        table_name = sys.argv[1]

    print(f"Setting up DynamoDB table: {table_name}")

    # Create table
    table = create_tv_show_table(table_name)

    # Ask if user wants to add sample data
    add_sample = input("Do you want to add sample data? (y/n): ").lower().strip()
    if add_sample in ['y', 'yes']:
        add_sample_data(table_name)

    print("Setup complete!")
    print(f"\nTo use this table, set the environment variable:")
    print(f"export DYNAMODB_TABLE={table_name}")
    print(f"\nOr run your Flask app with:")
    print(f"DYNAMODB_TABLE={table_name} python app.py")