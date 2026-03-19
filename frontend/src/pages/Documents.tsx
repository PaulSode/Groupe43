import React, { useState, useEffect } from 'react';
import { documentsAPI, incoherencesAPI } from '../api/client';
import { Document, Incoherence, DocumentType } from '../types';
import DocumentViewer from '../components/DocumentViewer';
import OcrConfidenceBadge from '../components/OcrConfidenceBadge';
import IncoherenceAlert from '../components/IncoherenceAlert';
import { DocumentFilePreview } from '../components/DocumentFilePreview';
import './Documents.css';

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [incoherences, setIncoherences] = useState<Incoherence[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<DocumentType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<Document['statut'] | 'all'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    filterDocumentsList();
  }, [documents, searchQuery, filterType, filterStatus]);

  const loadDocuments = async () => {
    try {
      const data = await documentsAPI.getAll();
      setDocuments(data);
    } catch (error) {
      console.error('Erreur lors du chargement des documents', error);
    } finally {
      setLoading(false);
    }
  };

  const filterDocumentsList = () => {
    let filtered = documents;

    if (filterType !== 'all') {
      filtered = filtered.filter(d => d.type === filterType);
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(d => d.statut === filterStatus);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(d =>
        d.filename.toLowerCase().includes(query) ||
        d.clientNom.toLowerCase().includes(query)
      );
    }

    setFilteredDocuments(filtered);
  };

  const handleViewDocument = async (doc: Document) => {
    setSelectedDocument(doc);
    try {
      const docIncoherences = await incoherencesAPI.getByDocument(doc.id);
      setIncoherences(docIncoherences);
    } catch (error) {
      console.error('Erreur lors du chargement des incohérences', error);
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await documentsAPI.reprocess(id);
      loadDocuments();
    } catch (error) {
      console.error('Erreur lors du retraitement', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
      try {
        await documentsAPI.delete(id);
        loadDocuments();
      } catch (error) {
        console.error('Erreur lors de la suppression', error);
      }
    }
  };

  const getTypeLabel = (type: DocumentType) => {
    const labels: Record<DocumentType, string> = {
      facture: 'Facture',
      devis: 'Devis',
      kbis: 'Kbis',
      urssaf: 'URSSAF',
      rib: 'RIB',
      siret: 'SIRET',
    };
    return labels[type];
  };

  const getStatusBadge = (statut: Document['statut']) => {
    const badges = {
      pending: { label: 'En attente', className: 'status-pending' },
      processed: { label: 'Traité', className: 'status-processed' },
      error: { label: 'Erreur', className: 'status-error' },
      manual_review: { label: 'Révision manuelle', className: 'status-manual' },
    };
    const badge = badges[statut];
    return <span className={`status-badge ${badge.className}`}>{badge.label}</span>;
  };

  const getCompletionStats = (type: string, extractedData?: Record<string, any>) => {
    const schema = (() => {
      switch (type.toLowerCase()) {
        case 'facture': return ['siret', 'siren', 'tva_intracom', 'montant_ht', 'montant_ttc', 'taux_tva', 'date_emission', 'numero_document'];
        case 'devis': return ['siret', 'siren', 'montant_ht', 'montant_ttc', 'taux_tva', 'date_emission', 'numero_document'];
        case 'urssaf': return ['siret', 'date_emission', 'date_expiration'];
        case 'kbis': return ['siret', 'siren', 'raison_sociale'];
        case 'rib': return ['iban', 'bic', 'raison_sociale'];
        default: return Object.keys(extractedData || {});
      }
    })();

    const total = schema.length;
    const filled = schema.filter(key => {
      const val = extractedData?.[key];
      return val !== null && val !== undefined && val !== '';
    }).length;

    return { total, filled, isComplete: total > 0 && total === filled };
  };

  if (loading) {
    return (
      <div className="documents-container">
        <div className="loading">Chargement des documents...</div>
      </div>
    );
  }

  return (
    <div className="documents-container">
      <div className="documents-header">
        <div className="header-content">
          <h1>Documents</h1>
          <p>{filteredDocuments.length} document{filteredDocuments.length > 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="documents-filters">
        <div className="search-box">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            type="text"
            placeholder="Rechercher par nom de fichier ou client..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="type-filters">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as DocumentType | 'all')}
            className="filter-select"
          >
            <option value="all">Tous les types</option>
            <option value="facture">Factures</option>
            <option value="devis">Devis</option>
            <option value="kbis">Kbis</option>
            <option value="urssaf">URSSAF</option>
            <option value="rib">RIB</option>
            <option value="siret">SIRET</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as Document['statut'] | 'all')}
            className="filter-select"
          >
            <option value="all">Tous les statuts</option>
            <option value="pending">En attente</option>
            <option value="processed">Traités</option>
            <option value="error">Erreurs</option>
            <option value="manual_review">Révision manuelle</option>
          </select>
        </div>
      </div>

      <div className="documents-grid">
        {filteredDocuments.map(doc => (
          <div key={doc.id} className="document-card">
            <div className="document-header">
              <div className="document-type-badge" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span>{getTypeLabel(doc.type)}</span>
                {(() => {
                  const stats = getCompletionStats(doc.type, doc.extractedData);
                  if (stats.total === 0) return null;
                  return (
                    <span style={{
                      backgroundColor: stats.isComplete ? '#d4edda' : '#fff3cd',
                      color: stats.isComplete ? '#155724' : '#856404',
                      padding: '2px 6px',
                      borderRadius: '10px',
                      fontSize: '0.85em',
                      fontWeight: 'bold'
                    }}>
                      {stats.filled}/{stats.total}
                    </span>
                  );
                })()}
              </div>
              {typeof doc.ocrConfidence === 'number' && (
                <OcrConfidenceBadge confidence={doc.ocrConfidence} />
              )}
            </div>

            <div className="document-body">
              <div className="document-icon" style={{ height: '140px', overflow: 'hidden', padding: '0' }}>
                <DocumentFilePreview docId={doc.id} filename={doc.filename} />
              </div>
              <h3 className="document-filename">{doc.filename}</h3>
              <p className="document-client">{doc.clientNom}</p>
              {doc.dateEmission && (
                <p className="document-date">
                  Émis le {new Date(doc.dateEmission).toLocaleDateString('fr-FR')}
                </p>
              )}
            </div>

            <div className="document-footer">
              <div className="document-status">
                {getStatusBadge(doc.statut)}
              </div>
              <div className="document-actions">
                <button
                  onClick={() => handleViewDocument(doc)}
                  className="btn-icon"
                  title="Voir le document"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
                {(doc.statut === 'error' || doc.statut === 'manual_review') && (
                  <button
                    onClick={() => handleReprocess(doc.id)}
                    className="btn-icon"
                    title="Retraiter"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="23 4 23 10 17 10"></polyline>
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                  </button>
                )}
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="btn-icon btn-danger"
                  title="Supprimer"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredDocuments.length === 0 && (
        <div className="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
          <p>Aucun document trouvé</p>
        </div>
      )}

      {selectedDocument && (
        <DocumentViewer
          document={selectedDocument}
          incoherences={incoherences}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  );
};

export default Documents;
