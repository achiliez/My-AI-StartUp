import boto3
import os
from dotenv import load_dotenv

load_dotenv()

textract = boto3.client(
    'textract',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

print(f"Testing Textract in region: '{os.getenv('AWS_REGION')}'")

try:
    # Just try to list adapters or something simple, or process a dummy doc
    # We'll use a dummy byte string which will fail with 'InvalidParameter' or 'UnsupportedDocument' 
    # but that proves Auth worked.
    # If auth fails, it will throw the UnrecognizedClientException again.
    response = textract.analyze_document(
        Document={'Bytes': b'not_a_real_pdf'},
        FeatureTypes=['TABLES']
    )
except Exception as e:
    print(f"\nCaught exception: {type(e).__name__}")
    print(f"Message: {e}")
