# services/ocr_service.py
import boto3
import os
from dotenv import load_dotenv

load_dotenv() # Load keys from .env file

class OCRService:
    def __init__(self):
        # Initialize AWS Textract Client
        self.client = boto3.client(
            'textract',
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

    def extract_text(self, file_bytes):
        """
        Sends file bytes to AWS and returns a simplified list of text lines.
        """
        try:
            response = self.client.analyze_document(
                Document={'Bytes': file_bytes},
                FeatureTypes=['TABLES'] 
            )
            
            # Simple extraction for the MVP: Just get the lines of text
            extracted_lines = []
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    extracted_lines.append(block['Text'])
            
            return {"status": "success", "data": extracted_lines}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
