from pydantic import BaseModel
from typing import Optional, List, Any
from enum import Enum


# ─────────────────────────────────────────────
# Modèles pipeline OCR (inchangés)
# ─────────────────────────────────────────────

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
    severity: str
    category: str
    message: str
    documents: List[str]


class VerificationReport(BaseModel):
    total_documents: int
    anomalies: List[Anomaly]
    is_coherent: bool


# ─────────────────────────────────────────────
# Modèles API — Authentification
# ─────────────────────────────────────────────

class UserLogin(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    password: str
    firstName: str
    lastName: str


class UserResponse(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    role: str


class TokenResponse(BaseModel):
    user: UserResponse
    token: str


# ─────────────────────────────────────────────
# Modèles API — Clients
# ─────────────────────────────────────────────

class ClientCreate(BaseModel):
    nom: str
    prenom: str = ""
    email: str = ""
    telephone: str = ""
    adresseFacturation: str = ""
    siret: str = ""
    siren: str = ""
    tva: str = ""
    statut: str = "actif"


class ClientUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresseFacturation: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    tva: Optional[str] = None
    statut: Optional[str] = None


class ClientResponse(BaseModel):
    id: str
    nom: str
    prenom: str
    email: str
    telephone: str
    adresseFacturation: str
    siret: str
    siren: str
    tva: str
    dateCreation: str
    statut: str


# ─────────────────────────────────────────────
# Modèles API — Documents
# ─────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    type: str
    clientId: str
    clientNom: str
    filename: str
    dateUpload: str
    dateEmission: Optional[str] = None
    dateExpiration: Optional[str] = None
    statut: str
    ocrConfidence: Optional[float] = None
    extractedData: Optional[dict[str, Any]] = None
    url: Optional[str] = None


class DocumentStatusUpdate(BaseModel):
    status: str
    extractedData: Optional[dict[str, Any]] = None


# ─────────────────────────────────────────────
# Modèles API — Incohérences
# ─────────────────────────────────────────────

class IncoherenceResponse(BaseModel):
    id: str
    documentId: str
    type: str
    severity: str
    message: str
    field: str
    expectedValue: Optional[str] = None
    actualValue: Optional[str] = None
    dateDetection: str


class DocumentWithIncoherencesResponse(BaseModel):
    document: DocumentResponse
    incoherences: List[IncoherenceResponse]


# ─────────────────────────────────────────────
# Modèles API — Dashboard
# ─────────────────────────────────────────────

class DashboardStatsResponse(BaseModel):
    totalDocuments: int
    documentsEnAttente: int
    documentsTraites: int
    documentsErreur: int
    totalClients: int
    incoherencesActives: int
    tauxReussiteOCR: float
