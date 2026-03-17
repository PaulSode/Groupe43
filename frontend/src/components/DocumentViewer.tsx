import React from 'react';
import { Document, Incoherence } from '../types';
import IncoherenceAlert from './IncoherenceAlert';
import OcrConfidenceBadge from './OcrConfidenceBadge';
import { incoherencesAPI } from '../api/client';
import './DocumentViewer.css';

interface DocumentViewerProps {
  document: Document;
  incoherences: Incoherence[];
  onClose: () => void;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({ document, incoherences, onClose }) => {
  const handleResolveIncoherence = async (id: string) => {
    try {
      await incoherencesAPI.resolve(id);
      window.location.reload();
    } catch (error) {
      console.error('Erreur lors de la résolution', error);
    }
  };

  return (
    <div className="viewer-overlay" onClick={onClose}>
      <div className="viewer-container" onClick={(e) => e.stopPropagation()}>
        <div className="viewer-header">
          <div className="viewer-title">
            <h2>{document.filename}</h2>
            <div className="viewer-meta">
              <span className="meta-item">{document.clientNom}</span>
              {document.dateEmission && (
                <span className="meta-item">
                  Émis le {new Date(document.dateEmission).toLocaleDateString('fr-FR')}
                </span>
              )}
              {document.ocrConfidence !== undefined && (
                <OcrConfidenceBadge confidence={document.ocrConfidence} />
              )}
            </div>
          </div>
          <button onClick={onClose} className="btn-close">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="viewer-body">
          <div className="viewer-main">
            <div className="document-preview">
              {document.url ? (
                <iframe
                  src={document.url}
                  title={document.filename}
                  className="document-iframe"
                />
              ) : (
                <div className="preview-placeholder">
                  <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  <p>Aperçu non disponible</p>
                </div>
              )}
            </div>
          </div>

          <div className="viewer-sidebar">
            {incoherences.length > 0 && (
              <IncoherenceAlert
                incoherences={incoherences}
                onResolve={handleResolveIncoherence}
              />
            )}

            {document.extractedData && (
              <div className="extracted-data">
                <h3>Données extraites</h3>
                <div className="data-list">
                  {Object.entries(document.extractedData).map(([key, value]) => (
                    <div key={key} className="data-item">
                      <span className="data-label">{key}</span>
                      <span className="data-value">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="document-info">
              <h3>Informations</h3>
              <div className="info-list">
                <div className="info-item">
                  <span className="info-label">Type</span>
                  <span className="info-value">{document.type}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Statut</span>
                  <span className="info-value">{document.statut}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Date d'upload</span>
                  <span className="info-value">
                    {new Date(document.dateUpload).toLocaleString('fr-FR')}
                  </span>
                </div>
                {document.dateExpiration && (
                  <div className="info-item">
                    <span className="info-label">Date d'expiration</span>
                    <span className="info-value">
                      {new Date(document.dateExpiration).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
