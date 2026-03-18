import os
from datetime import datetime, timezone
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "admin123")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "Data_Mongodb")


def _get_client() -> MongoClient:
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    return MongoClient(uri)


def get_db():
    client = _get_client()
    return client[MONGO_DB]


def save_raw_document(file_id: str, filename: str, file_path: str, raw_text: str) -> str:
    """Zone Raw — sauvegarde l'image originale (GridFS) + le texte OCR brut."""
    db = get_db()
    fs = GridFS(db, collection="images_raw")

    with open(file_path, "rb") as f:
        image_grid_id = fs.put(
            f,
            filename=filename,
            file_id=file_id,
            content_type=_guess_content_type(filename),
        )

    doc = {
        "file_id": file_id,
        "filename": filename,
        "image_grid_id": image_grid_id,
        "raw_text": raw_text,
        "zone": "raw",
        "created_at": datetime.now(timezone.utc),
    }
    result = db["ocr_raw"].insert_one(doc)
    return str(result.inserted_id)


def _guess_content_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def save_extracted_data(file_id: str, filename: str, doc_type: str,
                        raw_text: str, fields: dict) -> str:
    """Zone Curated — sauvegarde les données structurées extraites."""
    db = get_db()
    doc = {
        "file_id": file_id,
        "filename": filename,
        "doc_type": doc_type,
        "raw_text": raw_text,
        "fields": fields,
        "zone": "curated",
        "created_at": datetime.now(timezone.utc),
    }
    result = db["ocr_curated"].insert_one(doc)
    return str(result.inserted_id)


def save_verification_report(report: dict) -> str:
    """Sauvegarde un rapport de vérification inter-documents."""
    db = get_db()
    report["created_at"] = datetime.now(timezone.utc)
    result = db["verification_reports"].insert_one(report)
    return str(result.inserted_id)
