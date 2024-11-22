from flask import Flask, jsonify, request, send_from_directory
from aws.cognito_utils import create_user_pool, create_app_client
from aws.dynamodb_utils import create_appointments_table, put_appointment
from aws.s3_utils import get_s3_client, create_bucket, upload_car_image
# from aws.sns_utils import send_notification
from aws.lambda_utils import invoke_lambda_function
import boto3
import uuid
import json
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='frontend', static_url_path='')

# AWS Configuration
REGION = 'us-east-1'
USER_POOL_ID = 'us-east-1_UE7n1qefK'
CLIENT_ID = '4f5arm0rb74afuvka4splvijrf'
BUCKET_NAME = 'autocare-images'
# SNS_TOPIC_ARN = None
APPOINTMENTS_TABLE = 'Appointments'

def init_aws_services():
    global USER_POOL_ID, CLIENT_ID, APPOINTMENTS_TABLE
    
    # Initialize S3 first
    s3_client = get_s3_client(REGION)
    if not s3_client:
        print("Failed to initialize S3 client")
        return False
        
    bucket = create_bucket(s3_client, BUCKET_NAME, REGION)
    if not bucket:
        print("Failed to create S3 bucket")
        return False
    
    print(f"Successfully created/verified bucket: {BUCKET_NAME}")
    
    # Initialize Cognito
    try:
        USER_POOL_ID = create_user_pool('AutoCareUserPool')
        CLIENT_ID = create_app_client(USER_POOL_ID)
    except Exception as e:
        print(f"Error initializing Cognito: {str(e)}")

    # Initialize SNS
    # try:
    #     sns = boto3.client('sns', region_name=REGION)
    #     topic = sns.create_topic(Name='appointment-notifications')
    #     SNS_TOPIC_ARN = topic['TopicArn']
    # except Exception as e:
    #     print(f"Error initializing SNS: {str(e)}")

    # Initialize DynamoDB
    try:
        APPOINTMENTS_TABLE = create_appointments_table()
    except Exception as e:
        print(f"Error initializing DynamoDB: {str(e)}")

    return True

# Call initialization before the first request
@app.before_request
def initialize():
    if not init_aws_services():
        print("WARNING: Failed to initialize AWS services")

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        # Verify token with Cognito
        try:
            cognito = boto3.client('cognito-idp', region_name=REGION)
            response = cognito.get_user(AccessToken=auth_header)
            return f(*args, **kwargs, user=response)
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated

# Routes
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
            
        cognito = boto3.client('cognito-idp', region_name=REGION)
        
        # Add password validation
        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
            
        try:
            response = cognito.sign_up(
                ClientId=CLIENT_ID,
                Username=data['email'],
                Password=data['password'],
                UserAttributes=[
                    {'Name': 'email', 'Value': data['email']}
                ]
            )
            print(f"Signup response: {response}")  # Debug logging
            return jsonify({'message': 'User registered successfully'}), 201
            
        except cognito.exceptions.UsernameExistsException:
            return jsonify({'error': 'User already exists'}), 400
        except cognito.exceptions.InvalidPasswordException as e:
            return jsonify({'error': str(e)}), 400
        except cognito.exceptions.InvalidParameterException as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Cognito signup error: {str(e)}")  # Debug logging
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        print(f"General signup error: {str(e)}")  # Debug logging
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        cognito = boto3.client('cognito-idp', region_name=REGION)
        
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': data['email'],
                'PASSWORD': data['password']
            }
        )
        
        return jsonify({
            'token': response['AuthenticationResult']['AccessToken'],
            'user': {'email': data['email']}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout(user):
    try:
        cognito = boto3.client('cognito-idp', region_name=REGION)
        auth_header = request.headers.get('Authorization')
        cognito.global_sign_out(AccessToken=auth_header)
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/upload-url', methods=['POST'])
@require_auth
def get_upload_url(user):
    try:
        s3_client = get_s3_client(REGION)
        if not s3_client:
            return jsonify({'error': 'S3 client initialization failed'}), 500
            
        data = request.json
        file_name = f"{uuid.uuid4()}-{data['fileName']}"
        
        # Verify bucket exists
        try:
            s3_client.head_bucket(Bucket=BUCKET_NAME)
        except Exception as e:
            return jsonify({'error': f'S3 bucket not found: {str(e)}'}), 500
            
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_name,
                'ContentType': data['fileType']
            },
            ExpiresIn=3600
        )
        
        image_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_name}"
        return jsonify({
            'uploadUrl': url,
            'imageUrl': image_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/appointments', methods=['GET'])
@require_auth
def get_appointments(user):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table('Appointments')
        
        response = table.query(
            IndexName='UserEmailIndex',
            KeyConditionExpression='userEmail = :email',
            ExpressionAttributeValues={':email': user['Username']}
        )
        
        return jsonify(response['Items'])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/appointments', methods=['POST'])
@require_auth
def create_appointment(user):
    try:
        data = request.json
        appointment_id = str(uuid.uuid4())
        
        # Validate appointment using Lambda
        validation_result = invoke_lambda_function(
            'validate_appointment',
            {
                'appointment': {
                    'date': data['date'],
                    'time': data['time'],
                    'serviceType': data['serviceType']
                }
            }
        )
        
        if not validation_result.get('isValid', False):
            return jsonify({'error': validation_result.get('message', 'Invalid appointment')}), 400
        
        # Store appointment in DynamoDB
        appointment_data = {
            'appointment_id': appointment_id,
            'userEmail': user['Username'],
            'carMake': data['carMake'],
            'carModel': data['carModel'],
            'carYear': data['carYear'],
            'serviceType': data['serviceType'],
            'date': data['date'],
            'time': data['time'],
            'description': data.get('description', ''),
            'imageUrl': data.get('imageUrl', ''),
            'status': 'Pending',
            'createdAt': datetime.utcnow().isoformat()
        }
        
        put_appointment(appointment_id, appointment_data)
        
        # Send SNS notification if requested
        # if data.get('notificationPreference'):
        #     message = (
        #         f"New appointment booked!\n"
        #         f"Service: {data['serviceType']}\n"
        #         f"Date: {data['date']}\n"
        #         f"Time: {data['time']}\n"
        #         f"Vehicle: {data['carYear']} {data['carMake']} {data['carModel']}"
        #     )
            
        #     send_notification(
        #         SNS_TOPIC_ARN,
        #         message,
        #         'New Service Appointment'
        #     )
        
        return jsonify(appointment_data), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True)
