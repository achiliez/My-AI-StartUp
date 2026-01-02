# services/ocr_service.py
import boto3
import os
from dotenv import load_dotenv

load_dotenv(override=True) # Load keys from .env file, overwriting system vars

class OCRService:
    def __init__(self):
        # Initialize AWS Textract Client
        # DEBUG: Print loaded keys (masked)
        key_id = os.getenv("AWS_ACCESS_KEY_ID")
        print(f"DEBUG: OCRService initialized. Region={os.getenv('AWS_REGION')}")
        print(f"DEBUG: Key ID ends with: ...{key_id[-4:] if key_id else 'None'}")

        self.client = boto3.client(
            'textract',
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=key_id,
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

    def extract_text(self, file_bytes):
        """
        Sends file bytes to AWS Textract (FORMS analysis) and returns structured data.
        """
        try:
            print("DEBUG: Sending document to Textract...")
            response = self.client.analyze_document(
                Document={'Bytes': file_bytes},
                FeatureTypes=['FORMS', 'TABLES'] 
            )
            
            # 1. Parse Key-Value pairs from Textract response
            kv_map = self._get_kv_map(response)
            print(f"DEBUG: Extracted {len(kv_map)} key-value pairs.")

            # 2. Extract raw lines (fallback/supplementary)
            extracted_lines = []
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    extracted_lines.append(block['Text'])
            
            # 3. Smart Mapping to Standard Fields
            structured_data = self._map_to_standard_fields(kv_map)
            
            # 4. Construct Final Response
            result = {
                "status": "success",
                "data": extracted_lines, # Keep raw lines for UI debugging
                "raw_forms": kv_map,     # Full extracted KV pairs
                **structured_data        # Spread mapped fields (shipper, consignee, etc.)
            }
            return result
            
        except Exception as e:
            print(f"ERROR: Textract failed: {e}")
            return {"status": "error", "message": str(e)}

    def _get_kv_map(self, response):
        """
        Navigates the Textract JSON to pair KEY blocks with VALUE blocks.
        Returns a dictionary: { "Shipper Name": "ACME Corp", "Date": "2024-01-01" }
        """
        blocks = response['Blocks']
        key_map = {} # ID -> Block
        value_map = {} # ID -> Block
        block_map = {} # ID -> Block (all blocks)

        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block

        kvs = {}

        for key_block in key_map.values():
            key_text = self._get_text(key_block, block_map)
            val_text = ""
            
            # Find the VALUE relationship
            if 'Relationships' in key_block:
                for rel in key_block['Relationships']:
                    if rel['Type'] == 'VALUE':
                        for val_id in rel['Ids']:
                            val_block = value_map.get(val_id)
                            if val_block:
                                val_text = self._get_text(val_block, block_map)
            
            if key_text and val_text:
                kvs[key_text.strip()] = val_text.strip()

        return kvs

    def _get_text(self, block, block_map):
        """
        Helper to extract text from a block by following its CHILD relationships to WORD blocks.
        """
        text = ""
        if 'Relationships' in block:
            for rel in block['Relationships']:
                if rel['Type'] == 'CHILD':
                    for child_id in rel['Ids']:
                        child = block_map.get(child_id)
                        if child and child['BlockType'] == 'WORD':
                            text += child['Text'] + " "
                        elif child and child['BlockType'] == 'SELECTION_ELEMENT':
                             if child['SelectionStatus'] == 'SELECTED':
                                text += "[X] "
        return text.strip()

    def _map_to_standard_fields(self, kv_map):
        """
        Heuristic mapping of dynamic OCR keys to fixed API fields.
        """
        # Normalize keys for easier matching (lowercase)
        normalized_kv = {k.lower(): v for k, v in kv_map.items()}
        
        # Define search terms for each field
        # We look for partial matches in the keys
        
        def find_value(keywords):
            for k, v in normalized_kv.items():
                if any(term in k for term in keywords):
                    return v
            return None

        return {
            "bol_number": find_value(["bill of lading", "bol #", "b/l no", "bol no"]),
            "shipper": find_value(["shipper", "exporter", "from:"]),
            "consignee": find_value(["consignee", "sold to", "ship to", "to:"]),
            "carrier": find_value(["carrier", "transport"]),
            "weight": find_value(["weight", "gross weight", "kgs", "lbs"]),
            "date": find_value(["date", "shipping date"]),
            "origin": find_value(["origin", "port of loading"]),
            "destination": find_value(["destination", "port of discharge"])
        }
