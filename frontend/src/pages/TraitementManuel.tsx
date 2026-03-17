import React, { useState, useEffect } from 'react';
import { documentsAPI } from '../api/client';
import { Document } from '../types';
import './TraitementManuel.css';

const TraitementManuel: React.FC = () => {
  const [pendingDocuments, setPendingDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPendingDocuments();
  }, []);

  const loadPendingDocuments = async () => {
    try {
      const data = await documentsAPI.getPendingManualReview();
      setPendingDocuments(data);
    } catch (error) {
      console.error('Erreur lors du chargement', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDocument = (doc: Document) => {
    setSelectedDocument(doc);
    setFormData(doc.extractedData || {});
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (!selectedDocument) return;

    setSaving(true);
    try {
      await documentsAPI.updateStatus(selectedDocument.id, 'processed');
      loadPendingDocuments();
      setSelectedDocument(null);
      setFormData({});
    } catch (error) {
      console.error('Erreur lors de l\'enregistrement', error);
    } finally {
      setSaving(false);
    }
  };

  const getFieldsByType = (type: Document['type']) => {
    const fields: Record<Document['type'], string[]> = {
      facture: ['numero', 'dateEmission', 'montantHT', 'montantTTC', 'tva', 'siret'],
      devis: ['numero', 'dateEmission', 'dateValidite', 'montantHT', 'montantTTC', 'siret'],
      kbis: ['denomination', 'siret', 'siren', 'formeJuridique', 'dateImmatriculation'],
      urssaf: ['siret', 'dateEmission', 'dateExpiration', 'statut'],
      rib: ['titulaire', 'iban', 'bic', 'banque'],
      siret: ['siret', 'siren', 'denomination', 'adresse'],
    };
    return fields[type] || [];
  };

  if (loading) {
    return (
      <div className="traitement-container">
        <div className="loading">Chargement des documents...</div>
      </div>
    );
  }

  return (
    <div className="traitement-container">
      <div className="traitement-header">
        <h1>Traitement manuel</h1>
        <p>{pendingDocuments.length} document{pendingDocuments.length > 1 ? 's' : ''} en attente</p>
      </div>

      <div className="traitement-content">
        <div className="documents-queue">
          <h3>File d'attente</h3>
          {pendingDocuments.length === 0 ? (
            <div className="queue-empty">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <p>Aucun document en attente</p>
            </div>
          ) : (
            <div className="queue-list">
              {pendingDocuments.map(doc => (
                <div
                  key={doc.id}
                  className={`queue-item ${selectedDocument?.id === doc.id ? 'selected' : ''}`}
                  onClick={() => handleSelectDocument(doc)}
                >
                  <div className="queue-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                  </div>
                  <div className="queue-info">
                    <div className="queue-filename">{doc.filename}</div>
                    <div className="queue-meta">
                      <span className="queue-type">{doc.type}</span>
                      <span className="queue-client">{doc.clientNom}</span>
                    </div>
                  </div>
                  {doc.ocrConfidence !== undefined && (
                    <div className="queue-confidence">
                      {doc.ocrConfidence}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="document-form">
          {selectedDocument ? (
            <>
              <div className="form-header">
                <h3>{selectedDocument.filename}</h3>
                <span className="form-type-badge">{selectedDocument.type}</span>
              </div>

              <div className="form-body">
                <div className="form-notice">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                  <p>Vérifiez et corrigez les informations extraites automatiquement</p>
                </div>

                <div className="form-fields">
                  {getFieldsByType(selectedDocument.type).map(field => (
                    <div key={field} className="form-group">
                      <label htmlFor={field}>
                        {field.charAt(0).toUpperCase() + field.slice(1).replace(/([A-Z])/g, ' $1')}
                      </label>
                      <input
                        id={field}
                        type="text"
                        value={formData[field] || ''}
                        onChange={(e) => handleChange(field, e.target.value)}
                        placeholder={`Saisir ${field}`}
                      />
                    </div>
                  ))}
                </div>

                <div className="form-actions">
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="btn-secondary"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleSave}
                    className="btn-primary"
                    disabled={saving}
                  >
                    {saving ? 'Enregistrement...' : 'Valider et enregistrer'}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="form-placeholder">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="9" y1="15" x2="15" y2="15"></line>
              </svg>
              <p>Sélectionnez un document à traiter</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TraitementManuel;
