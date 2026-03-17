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

export type DocumentType = 'facture' | 'devis' | 'kbis' | 'urssaf' | 'rib' | 'siret';

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

export interface Incoherence {
  id: string;
  documentId: string;
  type: 'siret_mismatch' | 'date_expired' | 'tva_invalid' | 'iban_invalid' | 'montant_incoherent';
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
