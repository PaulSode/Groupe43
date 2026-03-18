import os
import json
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from api.database import get_db
from api.dependencies import get_current_user
from api.models import DocumentResponse, DocumentStatusUpdate, DocType

router = APIRouter(tags=["Documents"])

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

    client_id = int(clientId) if clientId else None
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

            statut = "processed" if confidence >= 70 else "manual_review"

            save_raw_document(file_id, uploaded_file.filename, file_path, raw_text)
            save_extracted_data(file_id, uploaded_file.filename, detected_type.value, raw_text, fields.model_dump())

            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO document
                       (type_document, id_client, filename, file_path, ocr_file_id,
                        date_emission, date_expiration, statut, ocr_confidence, raw_text, extracted_data)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       RETURNING id_document, date_upload""",
                    (
                        detected_type.value, client_id, uploaded_file.filename, file_path,
                        file_id, fields.date_emission, fields.date_expiration,
                        statut, confidence, raw_text, json.dumps(fields.model_dump()),
                    ),
                )
                inserted = cur.fetchone()

            _generate_incoherences(inserted["id_document"], detected_type.value, fields.model_dump(), client_id)

            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(f"{_SELECT_DOC} WHERE d.id_document = %s", (inserted["id_document"],))
                results.append(_row_to_document(cur.fetchone()))

        except Exception:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO document (type_document, id_client, filename, file_path, statut)
                       VALUES ('inconnu', %s, %s, %s, 'error')""",
                    (client_id, uploaded_file.filename, file_path),
                )

    return results


@router.patch("/documents/{doc_id}/status", response_model=DocumentResponse)
def update_document_status(doc_id: int, data: DocumentStatusUpdate, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE document SET statut = %s WHERE id_document = %s", (data.status, doc_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Document introuvable")
        cur.execute(f"{_SELECT_DOC} WHERE d.id_document = %s", (doc_id,))
        return _row_to_document(cur.fetchone())


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
    detected_type = classifier.classify(raw_text)
    fields = extractor.extract(raw_text, detected_type)

    statut = "processed" if confidence >= 70 else "manual_review"
    file_id = doc.get("ocr_file_id") or str(uuid.uuid4())

    save_raw_document(file_id, doc["filename"], doc["file_path"], raw_text)
    save_extracted_data(file_id, doc["filename"], detected_type.value, raw_text, fields.model_dump())

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE document SET type_document=%s, statut=%s, ocr_confidence=%s,
               raw_text=%s, extracted_data=%s, date_emission=%s, date_expiration=%s,
               ocr_file_id=%s
               WHERE id_document=%s""",
            (detected_type.value, statut, confidence, raw_text,
             json.dumps(fields.model_dump()), fields.date_emission, fields.date_expiration,
             file_id, doc_id),
        )
        cur.execute("DELETE FROM incoherence WHERE id_document = %s", (doc_id,))

    _generate_incoherences(doc_id, detected_type.value, fields.model_dump(), doc.get("id_client"))

    with get_db() as conn:
        cur = conn.cursor()
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

def _generate_incoherences(doc_id: int, doc_type: str, fields: dict, client_id: int | None):
    anomalies = []

    siret = fields.get("siret")
    if siret:
        cleaned = siret.replace(" ", "")
        if len(cleaned) != 14 or not cleaned.isdigit():
            anomalies.append(("siret_mismatch", "high", "Format SIRET invalide", "siret", "", siret))
        elif not _luhn_check(cleaned):
            anomalies.append(("siret_mismatch", "medium", "Le SIRET ne passe pas la validation Luhn", "siret", "", siret))

    if fields.get("montant_ht") and fields.get("montant_ttc") and fields.get("taux_tva"):
        try:
            ht = float(fields["montant_ht"])
            ttc = float(fields["montant_ttc"])
            taux = float(fields["taux_tva"].replace("%", ""))
            expected = round(ht * (1 + taux / 100), 2)
            if abs(expected - ttc) > 0.02:
                anomalies.append((
                    "montant_incoherent", "high",
                    f"HT={ht}€ × TVA {taux}% = {expected}€ attendu, mais {ttc}€ trouvé",
                    "montantTTC", str(expected), str(ttc),
                ))
        except (ValueError, TypeError):
            pass

    tva = fields.get("tva_intracom")
    if tva:
        cleaned = tva.replace(" ", "").upper()
        if not (cleaned.startswith("FR") and len(cleaned) == 13):
            anomalies.append(("tva_invalid", "medium", f"Numéro TVA intracommunautaire invalide : {tva}", "tva", "", tva))

    if client_id and siret:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT d.extracted_data->>'siret' AS other_siret, d.filename
                   FROM document d
                   WHERE d.id_client = %s AND d.id_document != %s
                         AND d.extracted_data->>'siret' IS NOT NULL""",
                (client_id, doc_id),
            )
            for row in cur.fetchall():
                if row["other_siret"] and row["other_siret"] != siret:
                    anomalies.append((
                        "siret_mismatch", "high",
                        f"SIRET différent du document '{row['filename']}' ({row['other_siret']} vs {siret})",
                        "siret", row["other_siret"], siret,
                    ))
                    break

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
