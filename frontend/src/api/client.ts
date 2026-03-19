import axios from 'axios';
import { User, Client, Document, Incoherence, DashboardStats, DocumentType } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (localStorage.getItem('mockUser')) {
    config.adapter = () =>
      Promise.resolve({
        data: getMockData(config.url, config.method),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      });
  }

  return config;
});



// Fonction pour retourner des données mockées
const getMockData = (url?: string, method?: string) => {
  if (!url) return {};

  // Dashboard stats
  if (url.includes('/dashboard/stats')) {
    return {
      totalDocuments: 247,
      documentsEnAttente: 12,
      documentsTraites: 221,
      documentsErreur: 14,
      totalClients: 58,
      incoherencesActives: 8,
      tauxReussiteOCR: 92,
    };
  }

  // Clients
  if (url.includes('/clients')) {
    return [
      {
        id: '1',
        nom: 'Martin',
        prenom: 'Sophie',
        email: 'sophie.martin@entreprise.fr',
        telephone: '06 12 34 56 78',
        adresseFacturation: '123 Rue de la Paix, 75001 Paris',
        siret: '12345678901234',
        siren: '123456789',
        tva: 'FR12345678901',
        dateCreation: '2024-01-15',
        statut: 'actif' as const,
      },
      {
        id: '2',
        nom: 'Dubois',
        prenom: 'Pierre',
        email: 'pierre.dubois@societe.com',
        telephone: '06 98 76 54 32',
        adresseFacturation: '45 Avenue des Champs, 69000 Lyon',
        siret: '98765432109876',
        siren: '987654321',
        tva: 'FR98765432109',
        dateCreation: '2024-02-20',
        statut: 'actif' as const,
      },
      {
        id: '3',
        nom: 'Bernard',
        prenom: 'Marie',
        email: 'marie.bernard@company.fr',
        telephone: '06 11 22 33 44',
        adresseFacturation: '78 Boulevard Victor Hugo, 33000 Bordeaux',
        siret: '11122233344455',
        siren: '111222333',
        tva: 'FR11122233344',
        dateCreation: '2024-03-10',
        statut: 'en_attente' as const,
      },
    ];
  }

  // Documents
  if (url.includes('/documents')) {
    return [
      {
        id: 'doc1',
        type: 'facture',
        clientId: '1',
        clientNom: 'Martin Sophie',
        filename: 'facture_2024_001.pdf',
        dateUpload: '2024-03-15T10:30:00',
        dateEmission: '2024-03-10',
        statut: 'processed',
        ocrConfidence: 95,
        extractedData: {
          numero: 'F2024-001',
          montantHT: '1000.00',
          montantTTC: '1200.00',
          tva: '200.00',
          siret: '12345678901234',
        },
      },
      {
        id: 'doc2',
        type: 'devis',
        clientId: '2',
        clientNom: 'Dubois Pierre',
        filename: 'devis_mars_2024.pdf',
        dateUpload: '2024-03-14T14:20:00',
        dateEmission: '2024-03-12',
        statut: 'processed',
        ocrConfidence: 88,
      },
      {
        id: 'doc3',
        type: 'kbis',
        clientId: '1',
        clientNom: 'Martin Sophie',
        filename: 'kbis_entreprise.pdf',
        dateUpload: '2024-03-13T09:15:00',
        statut: 'manual_review',
        ocrConfidence: 65,
      },
      {
        id: 'doc4',
        type: 'urssaf',
        clientId: '3',
        clientNom: 'Bernard Marie',
        filename: 'attestation_urssaf.pdf',
        dateUpload: '2024-03-12T16:45:00',
        dateEmission: '2024-02-28',
        dateExpiration: '2024-05-31',
        statut: 'processed',
        ocrConfidence: 92,
      },
    ];
  }

  // Documents en attente de traitement manuel
  if (url.includes('/manual-review')) {
    return [
      {
        id: 'doc3',
        type: 'kbis',
        clientId: '1',
        clientNom: 'Martin Sophie',
        filename: 'kbis_entreprise.pdf',
        dateUpload: '2024-03-13T09:15:00',
        statut: 'manual_review',
        ocrConfidence: 65,
        extractedData: {
          denomination: 'ENTREPRISE MARTIN',
          siret: '12345678901234',
        },
      },
    ];
  }

  // Incohérences
  if (url.includes('/incoherences')) {
    return [
      {
        id: 'inc1',
        documentId: 'doc1',
        type: 'date_expired',
        severity: 'medium',
        message: 'L\'attestation URSSAF a expiré',
        field: 'dateExpiration',
        actualValue: '2024-01-31',
        dateDetection: '2024-03-15',
      },
    ];
  }

  return {};
};

export const authAPI = {
  login: async (email: string, password: string): Promise<{ user: User; token: string }> => {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (email: string, password: string, firstName: string, lastName: string): Promise<{ user: User; token: string }> => {
    const response = await apiClient.post('/auth/register', { email, password, firstName, lastName });
    return response.data;
  },

  verify: async (token: string): Promise<User> => {
    const response = await apiClient.get('/auth/verify', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
};

export const clientsAPI = {
  getAll: async (): Promise<Client[]> => {
    const response = await apiClient.get('/clients');
    return response.data;
  },

  getById: async (id: string): Promise<Client> => {
    const response = await apiClient.get(`/clients/${id}`);
    return response.data;
  },

  create: async (client: Omit<Client, 'id' | 'dateCreation'>): Promise<Client> => {
    const response = await apiClient.post('/clients', client);
    return response.data;
  },

  update: async (id: string, client: Partial<Client>): Promise<Client> => {
    const response = await apiClient.put(`/clients/${id}`, client);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/clients/${id}`);
  },

  search: async (query: string): Promise<Client[]> => {
    const response = await apiClient.get('/clients/search', { params: { q: query } });
    return response.data;
  },
};

export const documentsAPI = {
  getAll: async (): Promise<Document[]> => {
    const response = await apiClient.get('/documents');
    return response.data;
  },

  getById: async (id: string): Promise<Document> => {
    const response = await apiClient.get(`/documents/${id}`);
    return response.data;
  },

  getFile: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/documents/${id}/file`, {
      responseType: 'blob'
    });
    return response.data;
  },

  getByClient: async (clientId: string): Promise<Document[]> => {
    const response = await apiClient.get(`/clients/${clientId}/documents`);
    return response.data;
  },

  upload: async (files: File[], clientId?: string): Promise<Document[]> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (clientId) {
      formData.append('clientId', clientId);
    }
    const response = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  uploadSingle: async (
    file: File,
    clientId: string | undefined,
    onUploadProgress: (pct: number) => void,
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('files', file);
    if (clientId) formData.append('clientId', clientId);
    const response = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total) onUploadProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
    return response.data[0];
  },

  updateStatus: async (id: string, status: string, extractedData?: Record<string, string>): Promise<{ document: Document; incoherences: Incoherence[] }> => {
    const body: Record<string, unknown> = { status };
    if (extractedData) body.extractedData = extractedData;
    const response = await apiClient.patch(`/documents/${id}/status`, body);
    return response.data;
  },

  reprocess: async (id: string): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/reprocess`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },

  getPendingManualReview: async (): Promise<Document[]> => {
    const response = await apiClient.get('/documents/manual-review');
    return response.data;
  },
};

export const incoherencesAPI = {
  getAll: async (): Promise<Incoherence[]> => {
    const response = await apiClient.get('/incoherences');
    return response.data;
  },

  getByDocument: async (documentId: string): Promise<Incoherence[]> => {
    const response = await apiClient.get(`/documents/${documentId}/incoherences`);
    return response.data;
  },

  resolve: async (id: string): Promise<void> => {
    await apiClient.post(`/incoherences/${id}/resolve`);
  },
};

export const dashboardAPI = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get('/dashboard/stats');
    return response.data;
  },
};
export default apiClient;