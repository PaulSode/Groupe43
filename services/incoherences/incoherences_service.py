from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.database import get_db
from api.dependencies import get_current_user
from api.models import IncoherenceResponse

router = APIRouter(tags=["Incohérences"])


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


@router.get("/incoherences", response_model=List[IncoherenceResponse])
def get_all_incoherences(_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM incoherence WHERE resolved = FALSE ORDER BY date_detection DESC"
        )
        return [_row_to_incoherence(r) for r in cur.fetchall()]


@router.get("/documents/{doc_id}/incoherences", response_model=List[IncoherenceResponse])
def get_incoherences_by_document(doc_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM incoherence WHERE id_document = %s ORDER BY date_detection DESC",
            (doc_id,),
        )
        return [_row_to_incoherence(r) for r in cur.fetchall()]


@router.post("/incoherences/{inc_id}/resolve", status_code=200)
def resolve_incoherence(inc_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE incoherence SET resolved = TRUE WHERE id_incoherence = %s", (inc_id,)
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Incohérence introuvable")
    return {"ok": True}
