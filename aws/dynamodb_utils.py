import boto3
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_appointments_table():
    # Check if the table already exists
    existing_tables = dynamodb.tables.all()
    for table in existing_tables:
        if table.name == 'Appointments':
            print("Table already exists.")
            return dynamodb.Table('Appointments')

    # Create the table
    table = dynamodb.create_table(
        TableName='Appointments',
        KeySchema=[{'AttributeName': 'appointment_id', 'KeyType': 'HASH'}],  # Partition key
        AttributeDefinitions=[{'AttributeName': 'appointment_id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    
    # Wait for the table to be created
    table.meta.client.get_waiter('table_exists').wait(TableName='Appointments')
    print("Table created successfully.")
    return table

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
