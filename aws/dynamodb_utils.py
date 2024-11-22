import boto3
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_appointments_table():
    # Check if the table already 
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

def put_appointment(appointment_id, car_model, appointment_time):
    table = dynamodb.Table('Appointments')
    table.put_item(
        Item={
            'appointment_id': appointment_id,
            'car_model': car_model,
            'appointment_time': appointment_time
        }
    )
    print(f"Appointment {appointment_id} added successfully.")

# Usage
create_appointments_table()
put_appointment('123', 'Toyota', '2024-11-21 10:00:00')
