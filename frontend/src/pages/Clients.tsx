import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { clientsAPI } from '../api/client';
import { Client } from '../types';
import FicheClient from '../components/FicheClient';
import ClientViewer from '../components/ClientViewer';
import './Clients.css';

const Clients: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [clients, setClients] = useState<Client[]>([]);
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [clientForDocuments, setClientForDocuments] = useState<Client | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<'all' | 'actif' | 'inactif' | 'en_attente'>('all');

  useEffect(() => { loadClients(); }, []);
  useEffect(() => { filterClientsList(); }, [clients, searchQuery, filterStatus]);
  useEffect(() => {
    if (location.state?.openCreateModal) {
      setShowModal(true);
      setSelectedClient(null);
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state?.openCreateModal, location.pathname, navigate]);

  const loadClients = async () => {
    try {
      const data = await clientsAPI.getAll();
      setClients(data);
    } catch (error) {
      console.error('Erreur lors du chargement des clients', error);
    } finally {
      setLoading(false);
    }
  };

  const filterClientsList = () => {
    let filtered = clients;
    if (filterStatus !== 'all') filtered = filtered.filter(c => c.statut === filterStatus);
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(c =>
        c.nom.toLowerCase().includes(query) ||
        c.prenom.toLowerCase().includes(query) ||
        c.email.toLowerCase().includes(query) ||
        c.siret.includes(query)
      );
    }
    setFilteredClients(filtered);
  };

  const handleCreateClient = () => { setSelectedClient(null); setShowModal(true); };
  const handleEditClient = (client: Client) => { setSelectedClient(client); setShowModal(true); };
  const handleClientSaved = () => { setShowModal(false); loadClients(); };

  const handleDeleteClient = async (id: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce client ?')) {
      try {
        await clientsAPI.delete(id);
        loadClients();
      } catch (error) {
        console.error('Erreur lors de la suppression', error);
      }
    }
  };

  const getStatusBadge = (statut: Client['statut']) => {
    const badges = {
      actif: { label: 'Actif', className: 'status-actif' },
      inactif: { label: 'Inactif', className: 'status-inactif' },
      en_attente: { label: 'En attente', className: 'status-attente' },
    };
    const badge = badges[statut];
    return <span className={`status-badge ${badge.className}`}>{badge.label}</span>;
  };

  if (loading) {
    return <div className="clients-container"><div className="loading">Chargement des clients...</div></div>;
  }

  return (
    <div className="clients-container">
      <div className="clients-header">
        <div className="header-content">
          <h1>Clients</h1>
          <p>{filteredClients.length} client{filteredClients.length > 1 ? 's' : ''}</p>
        </div>
        <button onClick={handleCreateClient} className="btn-primary">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Nouveau client
        </button>
      </div>

      <div className="clients-filters">
        <div className="search-box">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            type="text"
            placeholder="Rechercher par nom, email, SIRET..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="status-filters">
          {(['all', 'actif', 'en_attente', 'inactif'] as const).map(status => (
            <button
              key={status}
              className={`filter-btn ${filterStatus === status ? 'active' : ''}`}
              onClick={() => setFilterStatus(status)}
            >
              {status === 'all' ? 'Tous' : status === 'actif' ? 'Actifs' : status === 'en_attente' ? 'En attente' : 'Inactifs'}
            </button>
          ))}
        </div>
      </div>

      <div className="clients-table-container">
        <table className="clients-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Téléphone</th>
              <th>SIRET</th>
              <th>Statut</th>
              <th>Date création</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredClients.map(client => (
              <tr key={client.id}>
                <td className="client-name">{client.nom} {client.prenom}</td>
                <td>{client.email}</td>
                <td>{client.telephone}</td>
                <td className="mono">{client.siret}</td>
                <td>{getStatusBadge(client.statut)}</td>
                <td>{new Date(client.dateCreation).toLocaleDateString('fr-FR')}</td>
                <td>
                  <div className="action-buttons">
                    <button
                      onClick={() => setClientForDocuments(client)}
                      className="btn-icon"
                      title="Voir les documents"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    </button>
                    <button
                      onClick={() => handleEditClient(client)}
                      className="btn-icon"
                      title="Modifier"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDeleteClient(client.id)}
                      className="btn-icon btn-danger"
                      title="Supprimer"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredClients.length === 0 && (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="8.5" cy="7" r="4"></circle>
              <line x1="20" y1="8" x2="20" y2="14"></line>
              <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
            <p>Aucun client trouvé</p>
          </div>
        )}
      </div>

      {showModal && (
        <FicheClient
          client={selectedClient}
          onClose={() => setShowModal(false)}
          onSave={handleClientSaved}
        />
      )}

      {clientForDocuments && (
        <ClientViewer
          client={clientForDocuments}
          onClose={() => setClientForDocuments(null)}
        />
      )}
    </div>
  );
};

export default Clients;
