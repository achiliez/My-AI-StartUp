# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from services.ocr_service import OCRService
import uvicorn

app = FastAPI(title="Logistics BoL Extractor")
ocr_service = OCRService()

@app.get("/")
def home():
    return {"message": "System is Online. Go to /docs to test."}

@app.post("/extract/bol")
async def extract_bill_of_lading(file: UploadFile = File(...)):
    """
    Endpoint: Upload a PDF/Image -> Get Extracted Data
    """
    # 1. Validate file type
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF/JPG/PNG allowed.")

    # 2. Read file
    file_bytes = await file.read()

    # 3. Process with OCR Service
    result = ocr_service.extract_text(file_bytes)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return result

# Allow running directly with `python main.py`
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
