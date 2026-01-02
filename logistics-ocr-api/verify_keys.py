import boto3
import os
from dotenv import load_dotenv

load_dotenv()

try:
    auth = boto3.client(
        'sts',
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    print("Checking credentials...")
    identity = auth.get_caller_identity()
    print("SUCCESS! Credentials are valid.")
    print(f"Account: {identity['Account']}")
    print(f"ARN: {identity['Arn']}")
except Exception as e:
    print("\nFAILED to authenticate.")
    print(f"Error: {e}")
