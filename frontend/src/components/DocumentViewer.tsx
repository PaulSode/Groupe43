import React from 'react';
import { Document, Incoherence } from '../types';
import IncoherenceAlert from './IncoherenceAlert';
import OcrConfidenceBadge from './OcrConfidenceBadge';
import { incoherencesAPI } from '../api/client';
import { DocumentFilePreview } from './DocumentFilePreview';
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

  const getSchema = (type: string) => {
    switch (type.toLowerCase()) {
      case 'facture':
        return ['siret', 'siren', 'tva_intracom', 'montant_ht', 'montant_ttc', 'taux_tva', 'date_emission', 'numero_document'];
      case 'devis':
        return ['siret', 'siren', 'montant_ht', 'montant_ttc', 'taux_tva', 'date_emission', 'numero_document'];
      case 'urssaf':
        return ['siret', 'date_emission', 'date_expiration'];
      case 'kbis':
        return ['siret', 'siren', 'raison_sociale'];
      case 'rib':
        return ['iban', 'bic', 'raison_sociale'];
      default:
        return Object.keys(document.extractedData || {});
    }
  };

  const expectedKeys = getSchema(document.type);
  const totalFields = expectedKeys.length;
  const filledFields = expectedKeys.filter(key => {
    const val = document?.extractedData?.[key];
    return val !== null && val !== undefined && val !== '';
  }).length;
  const isComplete = totalFields > 0 && filledFields === totalFields;

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
              {typeof document.ocrConfidence === 'number' && (
                <OcrConfidenceBadge confidence={document.ocrConfidence} />
              )}
              {totalFields > 0 && (
                <span className="meta-item" style={{
                  backgroundColor: isComplete ? '#d4edda' : '#fff3cd',
                  color: isComplete ? '#155724' : '#856404',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '0.85em',
                  fontWeight: 'bold',
                  marginLeft: '8px'
                }}>
                  Complétude : {filledFields}/{totalFields}
                </span>
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
            <div className="document-preview" style={{ width: '100%', height: '100%', backgroundColor: '#f8f9fa' }}>
               <DocumentFilePreview docId={document.id} filename={document.filename} className="document-iframe" />
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
                  {expectedKeys.map((key) => {
                    const value = document.extractedData?.[key];
                    const isMissing = value === null || value === undefined || value === '';
                    
                    return (
                      <div key={key} className="data-item">
                        <span className="data-label" style={{ textTransform: 'capitalize' }}>
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="data-value" style={{ 
                          color: isMissing ? '#dc3545' : 'inherit',
                          fontWeight: isMissing ? 'bold' : 'normal'
                        }}>
                          {isMissing ? 'NON DÉTECTÉ' : String(value)}
                        </span>
                      </div>
                    );
                  })}
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
