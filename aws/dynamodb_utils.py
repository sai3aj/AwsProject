import boto3
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_appointments_table():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Check if table exists
        existing_tables = dynamodb.tables.all()
        if any(table.name == 'Appointments' for table in existing_tables):
            return dynamodb.Table('Appointments')

        # Create table with GSI
        table = dynamodb.create_table(
            TableName='Appointments',
            KeySchema=[
                {'AttributeName': 'appointment_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'appointment_id', 'AttributeType': 'S'},
                {'AttributeName': 'userEmail', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserEmailIndex',
                    'KeySchema': [
                        {'AttributeName': 'userEmail', 'KeyType': 'HASH'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for the table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName='Appointments')
        print("Appointments table created successfully with GSI")
        return table
        
    except Exception as e:
        print(f"Error creating appointments table: {str(e)}")
        raise e

def put_appointment(appointment_id, appointment_data):
    try:
        # Ensure appointment_id is in the data
        appointment_data['appointment_id'] = appointment_id
        
        table = dynamodb.Table('Appointments')
        table.put_item(Item=appointment_data)
        print(f"Appointment {appointment_id} added successfully.")
    except Exception as e:
        print(f"Error putting appointment in DynamoDB: {str(e)}")
        raise e

table = dynamodb.Table('Appointments')
