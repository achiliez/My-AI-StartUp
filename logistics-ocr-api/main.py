# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.ocr_service import OCRService
import uvicorn

app = FastAPI(title="Logistics BoL Extractor")

# Configure CORS for UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React Static Files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Ensure the build directory exists
build_dir = os.path.join(os.path.dirname(__file__), "textract-spark", "dist")
if os.path.exists(build_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(build_dir, "assets")), name="assets")

ocr_service = OCRService()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "System is Online"}

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

# SPA Catch-all route (Must be last)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # API routes are already handled above. If we get here, it's a frontend route.
    # However, we should be careful about API 404s.
    # But since we defined specific API routes, anything else matching this will fall through.
    # If the user requests /docs, FastAPI handles it before this catch-all?
    # No, /docs is a route.
    if full_path.startswith("api") or full_path.startswith("extract"):
         raise HTTPException(status_code=404, detail="API endpoint not found")
    
    if os.path.exists(build_dir):
        return FileResponse(os.path.join(build_dir, "index.html"))
    return {"message": "Frontend not built. Please run `npm run build` in textract-spark directory."}

# Allow running directly with `python main.py`
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
