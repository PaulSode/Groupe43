from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class DocType(str, Enum):
    FACTURE = "facture"
    DEVIS = "devis"
    ATTESTATION_SIRET = "attestation_siret"
    ATTESTATION_VIGILANCE = "attestation_vigilance"
    KBIS = "kbis"
    RIB = "rib"
    INCONNU = "inconnu"


class ExtractedFields(BaseModel):
    siret: Optional[str] = None
    siren: Optional[str] = None
    tva_intracom: Optional[str] = None
    montant_ht: Optional[str] = None
    montant_ttc: Optional[str] = None
    taux_tva: Optional[str] = None
    date_emission: Optional[str] = None
    date_expiration: Optional[str] = None
    numero_document: Optional[str] = None
    raison_sociale: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None


class ExtractionResult(BaseModel):
    file_id: str
    filename: str
    doc_type: DocType
    raw_text: str
    fields: ExtractedFields


class Anomaly(BaseModel):
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    documents: List[str]


class VerificationReport(BaseModel):
    total_documents: int
    anomalies: List[Anomaly]
    is_coherent: bool
