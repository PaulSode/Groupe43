from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from api.database import get_db
from api.dependencies import get_current_user
from api.models import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


def _row_to_client(row: dict) -> dict:
    return {
        "id": str(row["id_client"]),
        "nom": row["nom"] or "",
        "prenom": row["prenom"] or "",
        "email": row["email"] or "",
        "telephone": row["telephone"] or "",
        "adresseFacturation": row["adresse_facturation"] or "",
        "siret": row["siret"] or "",
        "siren": row["siren"] or "",
        "tva": row["tva_intracom"] or "",
        "dateCreation": row["date_creation"].isoformat() if row["date_creation"] else "",
        "statut": row["statut"] or "actif",
    }


@router.get("", response_model=List[ClientResponse])
def get_all_clients(_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM client ORDER BY date_creation DESC")
        return [_row_to_client(r) for r in cur.fetchall()]


@router.get("/search", response_model=List[ClientResponse])
def search_clients(q: str = Query(""), _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        like = f"%{q}%"
        cur.execute(
            """SELECT * FROM client
               WHERE nom ILIKE %s OR prenom ILIKE %s OR email ILIKE %s
                     OR siret ILIKE %s OR siren ILIKE %s
               ORDER BY date_creation DESC""",
            (like, like, like, like, like),
        )
        return [_row_to_client(r) for r in cur.fetchall()]


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM client WHERE id_client = %s", (client_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Client introuvable")
    return _row_to_client(row)


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(data: ClientCreate, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO client (nom, prenom, email, telephone, adresse_facturation,
                                   siret, siren, tva_intracom, statut)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (data.nom, data.prenom, data.email, data.telephone,
             data.adresseFacturation, data.siret, data.siren, data.tva, data.statut),
        )
        return _row_to_client(cur.fetchone())


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, data: ClientUpdate, _user: dict = Depends(get_current_user)):
    updates = {}
    field_map = {
        "nom": "nom", "prenom": "prenom", "email": "email",
        "telephone": "telephone", "adresseFacturation": "adresse_facturation",
        "siret": "siret", "siren": "siren", "tva": "tva_intracom", "statut": "statut",
    }
    for pydantic_field, db_col in field_map.items():
        val = getattr(data, pydantic_field)
        if val is not None:
            updates[db_col] = val

    if not updates:
        raise HTTPException(400, "Aucun champ à mettre à jour")

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [client_id]

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE client SET {set_clause} WHERE id_client = %s RETURNING *", values)
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Client introuvable")

    _recheck_all_client_documents(client_id)

    return _row_to_client(row)


def _recheck_all_client_documents(client_id: int):
    from documents.documents_service import _recheck_document
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id_document FROM document WHERE id_client = %s AND extracted_data IS NOT NULL", (client_id,))
        doc_ids = [r["id_document"] for r in cur.fetchall()]

    for doc_id in doc_ids:
        _recheck_document(doc_id, client_id)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, _user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM client WHERE id_client = %s", (client_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Client introuvable")
