import os
import json
import shutil
import uuid
from typing import List, Optional
from fastapi.responses import Response
import gridfs
from datalake.mongo_client import get_db as get_mongo_db

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from api.database import get_db
from api.dependencies import get_current_user
from api.models import DocumentResponse, DocumentStatusUpdate, DocumentWithIncoherencesResponse, IncoherenceResponse, DocType

router = APIRouter(tags=["Documents"])


def _row_to_incoherence(row: dict) -> dict:
    return {
        "id": str(row["id_incoherence"]),
        "documentId": str(row["id_document"]),
        "type": row["type_incoherence"],
        "severity": row["severity"],
        "message": row["message"],
        "field": row["field"] or "",
        "expectedValue": row.get("expected_value"),
        "actualValue": row.get("actual_value"),
        "dateDetection": row["date_detection"].isoformat() if row.get("date_detection") else "",
    }

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".pdf"}

DOC_TYPE_TO_FRONTEND = {
    "attestation_vigilance": "urssaf",
    "attestation_siret": "siret",
}
FRONTEND_TO_DOC_TYPE = {v: k for k, v in DOC_TYPE_TO_FRONTEND.items()}


def _map_type_to_frontend(backend_type: str) -> str:
    return DOC_TYPE_TO_FRONTEND.get(backend_type, backend_type)


def _map_type_from_frontend(frontend_type: str) -> str:
    return FRONTEND_TO_DOC_TYPE.get(frontend_type, frontend_type)


def _row_to_document(row: dict) -> dict:
    client_nom = ""
    if "client_nom" in row and row["client_nom"]:
        parts = [row["client_nom"]]
        if row.get("client_prenom"):
            parts.append(row["client_prenom"])
        client_nom = " ".join(parts)

    return {
        "id": str(row["id_document"]),
        "type": _map_type_to_frontend(row["type_document"]),
        "clientId": str(row["id_client"]) if row.get("id_client") else "",
        "clientNom": client_nom,
        "filename": row["filename"] or "",
        "dateUpload": row["date_upload"].isoformat() if row.get("date_upload") else "",
        "dateEmission": row.get("date_emission"),
        "dateExpiration": row.get("date_expiration"),
        "statut": row["statut"] or "pending",
        "ocrConfidence": float(row["ocr_confidence"]) if row.get("ocr_confidence") is not None else None,
        "extractedData": row.get("extracted_data"),
        "url": None,
    }


_SELECT_DOC = """
    SELECT d.*, c.nom AS client_nom, c.prenom AS client_prenom
    FROM document d
    LEFT JOIN client c ON d.id_client = c.id_client
"""


@router.get("/documents", response_model=List[DocumentResponse])
def get_all_documents(_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"{_SELECT_DOC} ORDER BY d.date_upload DESC")
        return [_row_to_document(r) for r in cur.fetchall()]


@router.get("/documents/manual-review", response_model=List[DocumentResponse])
def get_manual_review_documents(_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"{_SELECT_DOC} WHERE d.statut = 'manual_review' ORDER BY d.date_upload DESC")
        return [_row_to_document(r) for r in cur.fetchall()]


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"{_SELECT_DOC} WHERE d.id_document = %s", (doc_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Document introuvable")
    return _row_to_document(row)


@router.get("/clients/{client_id}/documents", response_model=List[DocumentResponse])
def get_documents_by_client(client_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"{_SELECT_DOC} WHERE d.id_client = %s ORDER BY d.date_upload DESC", (client_id,))
        return [_row_to_document(r) for r in cur.fetchall()]

@router.get("/documents/{doc_id}/file")
def get_document_file(doc_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ocr_file_id, file_path, filename FROM document WHERE id_document = %s", (doc_id,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Document introuvable")

    def _mime(name: str) -> str:
        ext = os.path.splitext(name)[1].lower()
        return {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".bmp": "image/bmp",
        }.get(ext, "application/octet-stream")

    if row.get("ocr_file_id"):
        db_mongo = get_mongo_db()
        fs = gridfs.GridFS(db_mongo, collection="images_raw")
        grid_out = fs.find_one({"file_id": row["ocr_file_id"]})
        if grid_out:
            mt = grid_out.content_type
            if mt in (None, "application/octet-stream") and row.get("filename"):
                mt = _mime(row["filename"])
            return Response(content=grid_out.read(), media_type=mt)

    if row.get("file_path") and os.path.exists(row["file_path"]):
        with open(row["file_path"], "rb") as f:
            mt = _mime(row.get("filename") or row["file_path"])
            return Response(content=f.read(), media_type=mt)

    raise HTTPException(404, "Fichier source introuvable")


@router.post("/documents/upload", response_model=List[DocumentResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    clientId: Optional[str] = Form(None),
    _user: dict = Depends(get_current_user),
):
    from ocr.ocr_service import OCRService
    from classifier.classifier import DocumentClassifier
    from extractor.extractor import DataExtractor
    from datalake.mongo_client import save_raw_document, save_extracted_data

    ocr_service = OCRService()
    classifier = DocumentClassifier()
    extractor = DataExtractor()

    if not clientId:
        raise HTTPException(400, "Un client doit être sélectionné")
    try:
        client_id = int(clientId)
    except (ValueError, TypeError):
        raise HTTPException(400, "ID client invalide")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id_client FROM client WHERE id_client = %s", (client_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Client introuvable")

    results = []

    for uploaded_file in files:
        ext = os.path.splitext(uploaded_file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

        with open(file_path, "wb") as f:
            shutil.copyfileobj(uploaded_file.file, f)

        try:
            raw_text, confidence = ocr_service.extract_text_with_confidence(file_path)
            detected_type = classifier.classify(raw_text)
            fields = extractor.extract(raw_text, detected_type)
            confidence = float(confidence)

            save_raw_document(file_id, uploaded_file.filename, file_path, raw_text)
            save_extracted_data(file_id, uploaded_file.filename, detected_type.value, raw_text, fields.model_dump())

            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO document
                       (type_document, id_client, filename, file_path, ocr_file_id,
                        date_emission, date_expiration, statut, ocr_confidence, raw_text, extracted_data)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       RETURNING id_document""",
                    (
                        detected_type.value, client_id, uploaded_file.filename, file_path,
                        file_id, fields.date_emission, fields.date_expiration,
                        "pending", confidence, raw_text, json.dumps(fields.model_dump()),
                    ),
                )
                doc_id = cur.fetchone()["id_document"]

            _generate_incoherences(doc_id, detected_type.value, fields.model_dump(), client_id)
            final_status = _evaluate_status(confidence, detected_type.value, fields.model_dump(), doc_id)
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE document SET statut = %s WHERE id_document = %s", (final_status, doc_id))
                cur.execute(f"{_SELECT_DOC} WHERE d.id_document = %s", (doc_id,))
                results.append(_row_to_document(cur.fetchone()))

        except Exception as e:
            import traceback
            print(f"[UPLOAD ERROR] {uploaded_file.filename}: {e}")
            traceback.print_exc()
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO document (type_document, id_client, filename, file_path, statut)
                       VALUES ('inconnu', %s, %s, %s, 'error')""",
                    (client_id, uploaded_file.filename, file_path),
                )

    return results


@router.patch("/documents/{doc_id}/status", response_model=DocumentWithIncoherencesResponse)
def update_document_status(doc_id: int, data: DocumentStatusUpdate, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id_client, type_document, ocr_confidence, extracted_data FROM document WHERE id_document = %s", (doc_id,))
        doc = cur.fetchone()
    if not doc:
        raise HTTPException(404, "Document introuvable")

    new_data = data.extractedData
    if new_data is not None:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE document SET extracted_data = %s WHERE id_document = %s",
                        (json.dumps(new_data), doc_id))

    client_id = doc.get("id_client")
    if client_id:
        fields = new_data if new_data else (doc.get("extracted_data") or {})
        if isinstance(fields, str):
            fields = json.loads(fields)

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM incoherence WHERE id_document = %s", (doc_id,))

        _generate_incoherences(doc_id, doc["type_document"], fields, client_id)

    confidence = float(doc["ocr_confidence"]) if doc.get("ocr_confidence") is not None else 100.0
    fields_for_status = new_data if new_data else (doc.get("extracted_data") or {})
    if isinstance(fields_for_status, str):
        fields_for_status = json.loads(fields_for_status)
    new_status = _evaluate_status(confidence, doc["type_document"], fields_for_status, doc_id)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE document SET statut = %s WHERE id_document = %s", (new_status, doc_id))
        cur.execute(f"{_SELECT_DOC} WHERE d.id_document = %s", (doc_id,))
        doc_resp = _row_to_document(cur.fetchone())

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM incoherence WHERE id_document = %s AND resolved = FALSE ORDER BY date_detection DESC", (doc_id,))
        incoherences = [_row_to_incoherence(r) for r in cur.fetchall()]

    return {"document": doc_resp, "incoherences": incoherences}


@router.post("/documents/{doc_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(doc_id: int, _user: dict = Depends(get_current_user)):
    from ocr.ocr_service import OCRService
    from classifier.classifier import DocumentClassifier
    from extractor.extractor import DataExtractor
    from datalake.mongo_client import save_raw_document, save_extracted_data

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM document WHERE id_document = %s", (doc_id,))
        doc = cur.fetchone()

    if not doc:
        raise HTTPException(404, "Document introuvable")
    if not doc["file_path"] or not os.path.exists(doc["file_path"]):
        raise HTTPException(400, "Fichier source introuvable sur le disque")

    ocr_service = OCRService()
    classifier = DocumentClassifier()
    extractor = DataExtractor()

    raw_text, confidence = ocr_service.extract_text_with_confidence(doc["file_path"])
    confidence = float(confidence)
    detected_type = classifier.classify(raw_text)
    fields = extractor.extract(raw_text, detected_type)
    file_id = doc.get("ocr_file_id") or str(uuid.uuid4())

    save_raw_document(file_id, doc["filename"], doc["file_path"], raw_text)
    save_extracted_data(file_id, doc["filename"], detected_type.value, raw_text, fields.model_dump())

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE document SET type_document=%s, statut='pending', ocr_confidence=%s,
               raw_text=%s, extracted_data=%s, date_emission=%s, date_expiration=%s,
               ocr_file_id=%s
               WHERE id_document=%s""",
            (detected_type.value, confidence, raw_text,
             json.dumps(fields.model_dump()), fields.date_emission, fields.date_expiration,
             file_id, doc_id),
        )
        cur.execute("DELETE FROM incoherence WHERE id_document = %s", (doc_id,))

    client_id = doc.get("id_client")
    if client_id:
        _generate_incoherences(doc_id, detected_type.value, fields.model_dump(), client_id)
    final_status = _evaluate_status(confidence, detected_type.value, fields.model_dump(), doc_id)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE document SET statut = %s WHERE id_document = %s", (final_status, doc_id))
        cur.execute(f"{_SELECT_DOC} WHERE d.id_document = %s", (doc_id,))
        return _row_to_document(cur.fetchone())


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT file_path FROM document WHERE id_document = %s", (doc_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Document introuvable")

        if row["file_path"] and os.path.exists(row["file_path"]):
            os.remove(row["file_path"])

        cur.execute("DELETE FROM document WHERE id_document = %s", (doc_id,))


# ── Génération automatique d'incohérences ──────────────────────

_FIELD_LABELS = {
    "siret": "SIRET", "siren": "SIREN",
    "tva_intracom": "TVA intracommunautaire", "raison_sociale": "Raison sociale",
}

_CLIENT_COMPARABLE_FIELDS = ["siret", "siren", "tva_intracom"]


def _generate_incoherences(doc_id: int, doc_type: str, fields: dict, client_id: int) -> int:
    """Génère les incohérences et renvoie le nombre créé."""
    anomalies: list[tuple] = []

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT siret, siren, tva_intracom FROM client WHERE id_client = %s", (client_id,))
        client_row = cur.fetchone() or {}

    # A. Document vs Client (client = référence)
    for field_key in _CLIENT_COMPARABLE_FIELDS:
        doc_val = fields.get(field_key)
        client_val = client_row.get(field_key)
        if doc_val and client_val and doc_val != client_val:
            label = _FIELD_LABELS.get(field_key, field_key)
            anomalies.append((
                "client_mismatch", "high",
                f"{label} du document ({doc_val}) différent de la fiche client ({client_val})",
                field_key, client_val, doc_val,
            ))

    # B. Inter-documents : SIRET facture vs attestation_siret
    if doc_type in ("facture", "attestation_siret"):
        other_type = "attestation_siret" if doc_type == "facture" else "facture"
        doc_siret = fields.get("siret")
        if doc_siret:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """SELECT d.filename, d.extracted_data->>'siret' AS other_siret
                       FROM document d
                       WHERE d.id_client = %s AND d.id_document != %s
                             AND d.type_document = %s
                             AND d.extracted_data->>'siret' IS NOT NULL""",
                    (client_id, doc_id, other_type),
                )
                for row in cur.fetchall():
                    if row["other_siret"] and row["other_siret"] != doc_siret:
                        anomalies.append((
                            "inter_doc_siret", "high",
                            f"SIRET différent de {row['filename']} ({row['other_siret']})",
                            "siret", row["other_siret"], doc_siret,
                        ))
                        break

    # C. Date d'expiration dépassée
    date_exp = fields.get("date_expiration")
    if date_exp:
        from datetime import datetime, date
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"]:
            try:
                exp = datetime.strptime(date_exp.strip(), fmt).date()
                if exp < date.today():
                    days = (date.today() - exp).days
                    anomalies.append(("date_expired", "high",
                        f"Document expiré depuis {days} jours (expiration : {date_exp})",
                        "date_expiration", "", date_exp))
                break
            except ValueError:
                continue

    if anomalies:
        with get_db() as conn:
            cur = conn.cursor()
            for type_inc, severity, message, field, expected, actual in anomalies:
                cur.execute(
                    """INSERT INTO incoherence
                       (id_document, type_incoherence, severity, message, field, expected_value, actual_value)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (doc_id, type_inc, severity, message, field, expected, actual),
                )

    return len(anomalies)


def _recheck_document(doc_id: int, client_id: int):
    """Supprime les anciennes incohérences, en génère de nouvelles, et recalcule le statut."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT type_document, extracted_data, ocr_confidence FROM document WHERE id_document = %s", (doc_id,))
        doc = cur.fetchone()
    if not doc or not doc.get("extracted_data"):
        return

    fields = doc["extracted_data"]
    if isinstance(fields, str):
        fields = json.loads(fields)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM incoherence WHERE id_document = %s", (doc_id,))

    nb = _generate_incoherences(doc_id, doc["type_document"], fields, client_id)
    confidence = float(doc["ocr_confidence"]) if doc.get("ocr_confidence") is not None else 100.0
    new_status = _evaluate_status(confidence, doc["type_document"], fields, doc_id)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE document SET statut = %s WHERE id_document = %s", (new_status, doc_id))


def _luhn_check(siret: str) -> bool:
    total = 0
    for i, c in enumerate(siret):
        n = int(c)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


SCHEMAS: dict[str, list[str]] = {
    "facture": ["siret", "siren", "tva_intracom", "montant_ht", "montant_ttc", "taux_tva", "date_emission", "numero_document"],
    "devis": ["siret", "siren", "montant_ht", "montant_ttc", "taux_tva", "date_emission", "numero_document"],
    "urssaf": ["siret", "date_emission", "date_expiration"],
    "attestation_vigilance": ["siret", "date_emission", "date_expiration"],
    "attestation_siret": ["siret", "siren", "raison_sociale"],
    "kbis": ["siret", "siren", "raison_sociale"],
    "rib": ["iban", "bic", "raison_sociale"],
}


def _evaluate_status(confidence: float, doc_type: str, fields: dict, doc_id: int | None = None) -> str:
    if confidence < 70:
        return "manual_review"

    expected = SCHEMAS.get(doc_type, list(fields.keys()))
    if any(not fields.get(f) for f in expected):
        return "manual_review"

    if doc_id is not None:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS n FROM incoherence WHERE id_document = %s AND resolved = FALSE", (doc_id,))
            if cur.fetchone()["n"] > 0:
                return "manual_review"

    return "processed"