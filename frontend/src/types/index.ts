export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'user';
}

export interface Client {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  telephone: string;
  adresseFacturation: string;
  siret: string;
  siren: string;
  tva: string;
  dateCreation: string;
  statut: 'actif' | 'inactif' | 'en_attente';
}

export type DocumentType = 'facture' | 'devis' | 'kbis' | 'urssaf' | 'rib' | 'attestation_siret' | 'attestation_vigilance' | 'inconnu';

export interface Document {
  id: string;
  type: DocumentType;
  clientId: string;
  clientNom: string;
  filename: string;
  dateUpload: string;
  dateEmission?: string;
  dateExpiration?: string;
  statut: 'pending' | 'processed' | 'error' | 'manual_review';
  ocrConfidence?: number;
  extractedData?: Record<string, any>;
  url?: string;
}

export type IncoherenceType = 'client_mismatch' | 'inter_doc_siret' | 'date_expired';

export interface Incoherence {
  id: string;
  documentId: string;
  type: IncoherenceType;
  severity: 'low' | 'medium' | 'high';
  message: string;
  field: string;
  expectedValue?: string;
  actualValue?: string;
  dateDetection: string;
}

export interface UploadStatus {
  filename: string;
  status: 'uploading' | 'processing' | 'success' | 'error';
  progress: number;
  error?: string;
  documentId?: string;
}

export interface DashboardStats {
  totalDocuments: number;
  documentsEnAttente: number;
  documentsTraites: number;
  documentsErreur: number;
  totalClients: number;
  incoherencesActives: number;
  tauxReussiteOCR: number;
}
