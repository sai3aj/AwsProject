import boto3

# Initialize a Cognito client
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

def create_user_pool(pool_name):
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

def create_app_client(user_pool_id):
    response = cognito_client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='car-app-client',
        GenerateSecret=False,
        ExplicitAuthFlows=[
            'ALLOW_USER_PASSWORD_AUTH',
            'ALLOW_REFRESH_TOKEN_AUTH',  # Add this line
        ],
    )
    return response['UserPoolClient']['ClientId']

# Usage
pool_id = create_user_pool('CarServiceUserPool')
app_client_id = create_app_client(pool_id)
print("User Pool ID:", pool_id)
print("App Client ID:", app_client_id)
