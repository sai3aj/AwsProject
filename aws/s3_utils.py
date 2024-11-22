import boto3
from botocore.exceptions import ClientError

def get_s3_client(region=None):
    """Initialize S3 client with optional region."""
    try:
        if region is None:
            s3_client = boto3.client('s3')
        else:
            s3_client = boto3.client('s3', region_name=region)
        
        # Test credentials by making a simple API call
        s3_client.list_buckets()
        return s3_client
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'InvalidAccessKeyId':
            print("Error: Invalid AWS access key. Please check your AWS credentials.")
        elif error_code == 'SignatureDoesNotMatch':
            print("Error: Invalid AWS secret key. Please check your AWS credentials.")
        elif error_code == 'AccessDenied':
            print("Error: Access denied. Please check your IAM permissions.")
        else:
            print(f"AWS Authentication Error: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"Error initializing S3 client: {str(e)}")
        print("Please ensure AWS credentials are properly configured:")
        print("1. Check ~/.aws/credentials file")
        print("2. Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("3. Verify IAM user has appropriate S3 permissions")
        return None

def create_bucket(s3_client, bucket_name, region=None):
    """Create an S3 bucket if it doesn't exist."""
    if s3_client is None:
        print("Error: S3 client not initialized. Please check AWS credentials and permissions.")
        return None

    try:
        # Check if the bucket already exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
        return bucket_name
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        
        if error_code == '404':  # Bucket doesn't exist
            try:
                if region is None or region == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    location = {'LocationConstraint': region}
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration=location
                    )
                print(f"Bucket '{bucket_name}' created successfully.")
                return bucket_name
            except ClientError as create_error:
                error = create_error.response.get('Error', {})
                if error.get('Code') == 'AccessDenied':
                    print("Error: Access denied. Please check your IAM permissions:")
                    print("- s3:CreateBucket")
                    print("- s3:PutBucketPolicy")
                    print("- s3:ListAllMyBuckets")
                elif error.get('Code') == 'InvalidBucketName':
                    print("Error: Invalid bucket name. Bucket names must:")
                    print("- Be between 3 and 63 characters long")
                    print("- Contain only lowercase letters, numbers, dots, and hyphens")
                    print("- Begin and end with a letter or number")
                elif error.get('Code') == 'BucketAlreadyExists':
                    print("Error: Bucket name already exists. Choose a different name.")
                else:
                    print(f"Error creating bucket: {error.get('Message', 'Unknown error')}")
                return None
        elif error_code == '403':  # Forbidden
            print("Error: Access forbidden. Please check:")
            print("1. AWS credentials are correct")
            print("2. IAM user has the following permissions:")
            print("   - s3:HeadBucket")
            print("   - s3:CreateBucket")
            print("   - s3:ListAllMyBuckets")
            print(f"Error details: {error_message}")
            return None
        else:
            print(f"Error checking bucket: {error_message}")
            return None

def upload_car_image(s3_client, bucket_name, image_name, file_path):
    """Upload a car image to the S3 bucket."""
    if s3_client is None:
        print("Error: S3 client not initialized. Please check AWS credentials and permissions.")
        return False

    try:
        # Remove any extra quotes from file path
        clean_path = file_path.strip('"\'')
        s3_client.upload_file(clean_path, bucket_name, image_name)
        print(f"File '{image_name}' uploaded to bucket '{bucket_name}' successfully.")
        return True
    except ClientError as e:
        error = e.response.get('Error', {})
        if error.get('Code') == 'AccessDenied':
            print("Error: Access denied. Please check your IAM permissions:")
            print("- s3:PutObject")
            print("- s3:PutObjectAcl")
        else:
            print(f"Error uploading file: {error.get('Message', 'Unknown error')}")
        return False
    except FileNotFoundError:
        print(f"Error: File not found at path: {clean_path}")
        print("Please verify the file path is correct and the file exists.")
        return False

# Example usage with proper error handling

# Initialize with specific region
region = 'us-east-1'  # Change this to your desired region
s3_client = get_s3_client(region)

if s3_client:  # Only proceed if client initialization was successful
    # Create bucket
    bucket_name = 'autocare-images1'
    bucket = create_bucket(s3_client, bucket_name, region)

    # Upload file if bucket exists
    if bucket:
        image_name = 'car.jpg'
        file_path = 'test_images/banner.jpeg'  # Use actual file path
        upload_car_image(s3_client, bucket_name, image_name, file_path)
