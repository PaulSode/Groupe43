import sys
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from api.models import ExtractionResult, VerificationReport
from ocr.ocr_service import OCRService
from classifier.classifier import DocumentClassifier
from extractor.extractor import DataExtractor
from validator.validator import DocumentValidator
from datalake.mongo_client import save_raw_document, save_extracted_data, save_verification_report

from auth.auth_service import router as auth_router
from clients.clients_service import router as clients_router
from documents.documents_service import router as documents_router
from incoherences.incoherences_service import router as incoherences_router
from dashboard.dashboard_service import router as dashboard_router

app = FastAPI(title="DocFlow — Extraction & Vérification de Documents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers applicatifs ────────────────────────────────────────
app.include_router(auth_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(incoherences_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

# ── Config upload pour le pipeline OCR ─────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ocr_service = OCRService()
classifier = DocumentClassifier()
extractor = DataExtractor()
validator = DocumentValidator()


# ── Endpoints pipeline OCR (existants, inchangés) ─────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract", response_model=ExtractionResult)
async def extract_document(file: UploadFile = File(...), doc_type: str = "auto"):
    """Extrait les informations clés d'un document via OCR."""
    allowed_extensions = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"Format non supporté: {ext}")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_text = ocr_service.extract_text(file_path)

        if doc_type != "auto":
            from api.models import DocType
            try:
                detected_type = DocType(doc_type)
            except ValueError:
                detected_type = classifier.classify(raw_text)
        else:
            detected_type = classifier.classify(raw_text)

        fields = extractor.extract(raw_text, detected_type)

        save_raw_document(file_id, file.filename, file_path, raw_text)
        save_extracted_data(
            file_id, file.filename, detected_type.value, raw_text, fields.model_dump()
        )

        return ExtractionResult(
            file_id=file_id,
            filename=file.filename,
            doc_type=detected_type,
            raw_text=raw_text,
            fields=fields,
        )
    except Exception as e:
        raise HTTPException(500, f"Erreur lors de l'extraction: {str(e)}")


@app.post("/api/verify", response_model=VerificationReport)
async def verify_documents(documents: List[ExtractionResult]):
    """Vérifie la cohérence inter-documents."""
    report = validator.validate(documents)
    save_verification_report(report.model_dump())
    return report
