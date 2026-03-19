import React, { useState, useEffect } from 'react';
import { documentsAPI, incoherencesAPI } from '../api/client';
import { Client, Document, DocumentType, Incoherence } from '../types';
import OcrConfidenceBadge from './OcrConfidenceBadge';
import DocumentViewer from './DocumentViewer';
import './ClientViewer.css';

interface ClientViewerProps {
  client: Client;
  onClose: () => void;
}

const ClientViewer: React.FC<ClientViewerProps> = ({ client, onClose }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [incoherences, setIncoherences] = useState<Incoherence[]>([]);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const data = await documentsAPI.getByClient(client.id);
        setDocuments(data);
      } catch (error) {
        console.error('Erreur lors du chargement des documents', error);
      } finally {
        setLoading(false);
      }
    };
    loadDocuments();
  }, [client.id]);

  const handleViewDocument = async (doc: Document) => {
    try {
      const data = await incoherencesAPI.getByDocument(doc.id);
      setIncoherences(data);
    } catch (error) {
      console.error('Erreur lors du chargement des incohérences', error);
      setIncoherences([]);
    }
    setSelectedDocument(doc);
  };

  const handleCloseViewer = () => {
    setSelectedDocument(null);
    setIncoherences([]);
  };

  const getTypeLabel = (type: DocumentType) => {
    const labels: Record<DocumentType, string> = {
      facture: 'Facture',
      devis: 'Devis',
      kbis: 'Kbis',
      urssaf: 'URSSAF',
      rib: 'RIB',
      attestation_siret: 'Attestation SIRET',
      attestation_vigilance: 'Attestation vigilance',
      inconnu: 'Inconnu',
    };
    return labels[type] || type;
  };

  const getStatusLabel = (statut: Document['statut']) => {
    const labels: Record<Document['statut'], string> = {
      pending: 'En attente',
      processed: 'Traité',
      error: 'Erreur',
      manual_review: 'Révision manuelle',
    };
    return labels[statut];
  };

  return (
    <>
      <div className="client-docs-overlay" onClick={onClose}>
        <div className="client-docs-modal" onClick={(e) => e.stopPropagation()}>

          <div className="client-docs-header">
            <div>
              <h2>Documents de {client.nom} {client.prenom}</h2>
              <p>
                {loading ? '…' : `${documents.length} document${documents.length > 1 ? 's' : ''}`}
              </p>
            </div>
            <button className="client-docs-btn-close" onClick={onClose}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div className="client-docs-body">
            {loading ? (
              <div className="client-docs-loading">
                <p>Chargement des documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="client-docs-empty">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                <p>Aucun document pour ce client</p>
              </div>
            ) : (
              <table className="client-docs-table">
                <thead>
                  <tr>
                    <th>Fichier</th>
                    <th>Type</th>
                    <th>Date d'upload</th>
                    <th>Statut</th>
                    <th>OCR</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>
                        <div className="client-docs-filename">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                          </svg>
                          {doc.filename}
                        </div>
                      </td>
                      <td>
                        <span className="client-docs-type-badge">
                          {getTypeLabel(doc.type)}
                        </span>
                      </td>
                      <td>{new Date(doc.dateUpload).toLocaleDateString('fr-FR')}</td>
                      <td>
                        <span className={`client-docs-status ${doc.statut}`}>
                          {getStatusLabel(doc.statut)}
                        </span>
                      </td>
                      <td>
                        {doc.ocrConfidence !== undefined
                          ? <OcrConfidenceBadge confidence={doc.ocrConfidence} />
                          : <span className="client-docs-no-ocr">—</span>
                        }
                      </td>
                      <td>
                        <button
                          className="client-docs-btn-view"
                          title="Voir le document"
                          onClick={() => handleViewDocument(doc)}
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                          </svg>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

        </div>
      </div>

      {selectedDocument && (
        <DocumentViewer
          document={selectedDocument}
          incoherences={incoherences}
          onClose={handleCloseViewer}
          onDocumentUpdated={(updatedDoc, newIncs) => {
            setDocuments(prev => prev.map(d => d.id === updatedDoc.id ? updatedDoc : d));
            setSelectedDocument(updatedDoc);
            setIncoherences(newIncs);
          }}
        />
      )}
    </>
  );
};

export default ClientViewer;