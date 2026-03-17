import React, { useState, useCallback } from 'react';
import { documentsAPI, clientsAPI } from '../api/client';
import { Client, UploadStatus } from '../types';
import DropZone from '../components/DropZone';
import './Upload.css';

const Upload: React.FC = () => {
  const [uploads, setUploads] = useState<UploadStatus[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showClientSearch, setShowClientSearch] = useState(false);

  const searchClients = useCallback(async (query: string) => {
    if (query.length < 2) {
      setClients([]);
      return;
    }
    try {
      const results = await clientsAPI.search(query);
      setClients(results);
    } catch (error) {
      console.error('Erreur lors de la recherche', error);
    }
  }, []);

  const handleFilesSelected = async (files: File[]) => {
    const newUploads: UploadStatus[] = files.map(file => ({
      filename: file.name,
      status: 'uploading',
      progress: 0,
    }));

    setUploads(prev => [...prev, ...newUploads]);

    try {
      const uploadedDocs = await documentsAPI.upload(
        files,
        selectedClient || undefined
      );

      setUploads(prev =>
        prev.map((upload, index) => {
          const doc = uploadedDocs[index];
          if (doc) {
            return {
              ...upload,
              status: 'success',
              progress: 100,
              documentId: doc.id,
            };
          }
          return upload;
        })
      );
    } catch (error) {
      setUploads(prev =>
        prev.map(upload => ({
          ...upload,
          status: 'error',
          error: 'Erreur lors de l\'upload',
        }))
      );
    }
  };

  const clearUploads = () => {
    setUploads([]);
  };

  const getStatusIcon = (status: UploadStatus['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return (
          <svg className="spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
          </svg>
        );
      case 'success':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success-color)" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        );
      case 'error':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--error-color)" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        );
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h1>Importer des documents</h1>
        <p>Glissez-déposez vos fichiers ou cliquez pour sélectionner</p>
      </div>

      <div className="upload-content">
        <div className="upload-options">
          <div className="option-group">
            <label>
              <input
                type="checkbox"
                checked={showClientSearch}
                onChange={(e) => {
                  setShowClientSearch(e.target.checked);
                  if (!e.target.checked) {
                    setSelectedClient('');
                    setSearchQuery('');
                    setClients([]);
                  }
                }}
              />
              <span>Associer à un client existant</span>
            </label>
          </div>

          {showClientSearch && (
            <div className="client-search">
              <input
                type="text"
                placeholder="Rechercher un client..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  searchClients(e.target.value);
                }}
              />
              {clients.length > 0 && (
                <div className="client-results">
                  {clients.map(client => (
                    <div
                      key={client.id}
                      className={`client-item ${selectedClient === client.id ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedClient(client.id);
                        setSearchQuery(`${client.nom} ${client.prenom}`);
                        setClients([]);
                      }}
                    >
                      <div className="client-name">
                        {client.nom} {client.prenom}
                      </div>
                      <div className="client-info">
                        {client.siret} • {client.email}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <DropZone onFilesSelected={handleFilesSelected} />

        {uploads.length > 0 && (
          <div className="uploads-list">
            <div className="uploads-header">
              <h3>Fichiers ({uploads.length})</h3>
              <button onClick={clearUploads} className="btn-clear">
                Effacer la liste
              </button>
            </div>
            <div className="uploads-items">
              {uploads.map((upload, index) => (
                <div key={index} className={`upload-item ${upload.status}`}>
                  <div className="upload-icon">
                    {getStatusIcon(upload.status)}
                  </div>
                  <div className="upload-info">
                    <div className="upload-filename">{upload.filename}</div>
                    {upload.error && (
                      <div className="upload-error">{upload.error}</div>
                    )}
                    {upload.status === 'success' && (
                      <div className="upload-success">Traitement en cours...</div>
                    )}
                  </div>
                  <div className="upload-progress">
                    {upload.progress}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Upload;
