import React, { useState, useMemo } from 'react';
import { Document, Incoherence } from '../types';
import IncoherenceAlert from './IncoherenceAlert';
import OcrConfidenceBadge from './OcrConfidenceBadge';
import { documentsAPI } from '../api/client';
import { DocumentFilePreview } from './DocumentFilePreview';
import './DocumentViewer.css';

interface DocumentViewerProps {
  document: Document;
  incoherences: Incoherence[];
  onClose: () => void;
  onDocumentUpdated?: (doc: Document, incs: Incoherence[]) => void;
}

const SCHEMAS: Record<string, string[]> = {
  facture: ['siret', 'siren', 'tva_intracom', 'montant_ht', 'montant_ttc', 'taux_tva', 'date_emission', 'numero_document'],
  devis: ['siret', 'siren', 'montant_ht', 'montant_ttc', 'taux_tva', 'date_emission', 'numero_document'],
  urssaf: ['siret', 'date_emission', 'date_expiration'],
  attestation_vigilance: ['siret', 'date_emission', 'date_expiration'],
  attestation_siret: ['siret', 'siren', 'raison_sociale'],
  kbis: ['siret', 'siren', 'raison_sociale'],
  rib: ['iban', 'bic', 'raison_sociale'],
};

const DocumentViewer: React.FC<DocumentViewerProps> = ({ document: doc, incoherences: initialIncoherences, onClose, onDocumentUpdated }) => {
  const [editedData, setEditedData] = useState<Record<string, string>>(doc.extractedData || {});
  const [liveIncoherences, setLiveIncoherences] = useState(initialIncoherences);
  const [currentDoc, setCurrentDoc] = useState(doc);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  const expectedKeys = SCHEMAS[doc.type.toLowerCase()] || Object.keys(doc.extractedData || {});

  const { totalFields, filledFields, isComplete } = useMemo(() => {
    const total = expectedKeys.length;
    const filled = expectedKeys.filter(k => {
      const v = editedData[k];
      return v !== null && v !== undefined && v !== '';
    }).length;
    return { totalFields: total, filledFields: filled, isComplete: total > 0 && filled === total };
  }, [expectedKeys, editedData]);

  const handleFix = (field: string, expectedValue: string, _incId: string) => {
    setEditedData(prev => ({ ...prev, [field]: expectedValue }));
    setDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const resp = await documentsAPI.updateStatus(currentDoc.id, currentDoc.statut, editedData);
      setCurrentDoc(resp.document);
      setLiveIncoherences(resp.incoherences);
      setEditedData(resp.document.extractedData || editedData);
      setDirty(false);
      onDocumentUpdated?.(resp.document, resp.incoherences);
    } catch (err) {
      console.error('Erreur lors de la sauvegarde', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="viewer-overlay" onClick={onClose}>
      <div className="viewer-container" onClick={(e) => e.stopPropagation()}>
        <div className="viewer-header">
          <div className="viewer-title">
            <h2>{currentDoc.filename}</h2>
            <div className="viewer-meta">
              <span className="meta-item">{currentDoc.clientNom}</span>
              {currentDoc.dateEmission && (
                <span className="meta-item">
                  Émis le {new Date(currentDoc.dateEmission).toLocaleDateString('fr-FR')}
                </span>
              )}
              {typeof currentDoc.ocrConfidence === 'number' && (
                <OcrConfidenceBadge confidence={currentDoc.ocrConfidence} />
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
               <DocumentFilePreview docId={currentDoc.id} filename={currentDoc.filename} className="document-iframe" />
            </div>
          </div>

          <div className="viewer-sidebar">
            {liveIncoherences.length > 0 && (
              <IncoherenceAlert
                incoherences={liveIncoherences}
                onFix={handleFix}
              />
            )}

            <div className="extracted-data">
              <h3>Données extraites</h3>
              <div className="data-list">
                {expectedKeys.map((key) => {
                  const value = editedData[key];
                  const isMissing = value === null || value === undefined || value === '';
                  const fieldInc = liveIncoherences.find(i => i.field === key);
                  const hasIncoherence = !!fieldInc;

                  const tooltipText = fieldInc
                    ? fieldInc.type === 'client_mismatch'
                      ? `Différent des données du client (${fieldInc.expectedValue})`
                      : fieldInc.message
                    : '';

                  return (
                    <div key={key} className={`data-item ${hasIncoherence ? 'data-item-warning' : ''}`}>
                      <span className="data-label">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className={`data-value ${isMissing ? 'data-value-missing' : ''} ${hasIncoherence ? 'data-value-warning' : ''}`}>
                        {hasIncoherence && (
                          <span className="warning-triangle" title={tooltipText}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" strokeWidth="1">
                              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                              <line x1="12" y1="9" x2="12" y2="13" stroke="white" strokeWidth="2"></line>
                              <line x1="12" y1="17" x2="12.01" y2="17" stroke="white" strokeWidth="2"></line>
                            </svg>
                          </span>
                        )}
                        {isMissing ? 'NON DÉTECTÉ' : value}
                      </span>
                    </div>
                  );
                })}
              </div>

              {dirty && (
                <button
                  className="btn-save-data"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? 'Sauvegarde...' : 'Sauvegarder les modifications'}
                </button>
              )}
            </div>

            <div className="document-info">
              <h3>Informations</h3>
              <div className="info-list">
                <div className="info-item">
                  <span className="info-label">Type</span>
                  <span className="info-value">{currentDoc.type}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Statut</span>
                  <span className="info-value">{currentDoc.statut}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Date d'upload</span>
                  <span className="info-value">
                    {new Date(currentDoc.dateUpload).toLocaleString('fr-FR')}
                  </span>
                </div>
                {currentDoc.dateExpiration && (
                  <div className="info-item">
                    <span className="info-label">Date d'expiration</span>
                    <span className="info-value">
                      {new Date(currentDoc.dateExpiration).toLocaleDateString('fr-FR')}
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
