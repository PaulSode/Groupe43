from fastapi import APIRouter, Depends

from api.database import get_db
from api.dependencies import get_current_user
from api.models import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_stats(_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS n FROM document")
        total_docs = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM document WHERE statut = 'pending'")
        en_attente = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM document WHERE statut = 'processed'")
        traites = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM document WHERE statut = 'error'")
        erreur = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM client")
        total_clients = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM incoherence WHERE resolved = FALSE")
        incoherences = cur.fetchone()["n"]

        cur.execute(
            "SELECT AVG(ocr_confidence) AS avg FROM document WHERE ocr_confidence IS NOT NULL"
        )
        avg_row = cur.fetchone()
        taux_ocr = float(avg_row["avg"]) if avg_row["avg"] is not None else 0.0

    return {
        "totalDocuments": total_docs,
        "documentsEnAttente": en_attente,
        "documentsTraites": traites,
        "documentsErreur": erreur,
        "totalClients": total_clients,
        "incoherencesActives": incoherences,
        "tauxReussiteOCR": round(taux_ocr, 1),
    }
