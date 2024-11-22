import boto3

# Initialize a Cognito client
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

def create_user_pool(pool_name):
    try:
        # List existing user pools
        response = cognito_client.list_user_pools(MaxResults=60)
        for pool in response['UserPools']:
            if pool['Name'] == pool_name:
                print(f"User pool {pool_name} already exists")
                return pool['Id']

        # Create new pool if it doesn't exist
        response = cognito_client.create_user_pool(
            PoolName=pool_name,
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': True
                }
            },
            AutoVerifiedAttributes=['email'],
            MfaConfiguration='OFF',
        )
        return response['UserPool']['Id']
    except Exception as e:
        print(f"Error creating/getting user pool: {str(e)}")
        return None

def create_app_client(user_pool_id):
    try:
        # List existing clients
        response = cognito_client.list_user_pool_clients(
            UserPoolId=user_pool_id,
            MaxResults=60
        )
        
        for client in response['UserPoolClients']:
            if client['ClientName'] == 'car-app-client':
                print("App client already exists")
                return client['ClientId']

        # Create new client if it doesn't exist
        response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='car-app-client',
            GenerateSecret=False,
            ExplicitAuthFlows=[
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
            ],
        )
        return response['UserPoolClient']['ClientId']
    except Exception as e:
        print(f"Error creating/getting app client: {str(e)}")
        return None

# Usage
pool_id = create_user_pool('CarServiceUserPool')
app_client_id = create_app_client(pool_id)
print("User Pool ID:", pool_id)
print("App Client ID:", app_client_id)
