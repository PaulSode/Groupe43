import React, { useState, useEffect } from 'react';
import { clientsAPI } from '../api/client';
import { Client } from '../types';
import './FicheClient.css';

interface FicheClientProps {
  client: Client | null;
  onClose: () => void;
  onSave: () => void;
}

const FicheClient: React.FC<FicheClientProps> = ({ client, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    adresseFacturation: '',
    siret: '',
    siren: '',
    tva: '',
    statut: 'actif' as Client['statut'],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (client) {
      setFormData({
        nom: client.nom,
        prenom: client.prenom,
        email: client.email,
        telephone: client.telephone,
        adresseFacturation: client.adresseFacturation,
        siret: client.siret,
        siren: client.siren,
        tva: client.tva,
        statut: client.statut,
      });
    }
  }, [client]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (client) {
        await clientsAPI.update(client.id, formData);
      } else {
        await clientsAPI.create(formData);
      }
      onSave();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Erreur lors de l\'enregistrement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{client ? 'Modifier le client' : 'Nouveau client'}</h2>
          <button onClick={onClose} className="btn-close">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {error && (
            <div className="form-error">
              {error}
            </div>
          )}

          <div className="form-section">
            <h3>Informations personnelles</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="nom">Nom *</label>
                <input
                  id="nom"
                  name="nom"
                  type="text"
                  value={formData.nom}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="prenom">Prénom *</label>
                <input
                  id="prenom"
                  name="prenom"
                  type="text"
                  value={formData.prenom}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="telephone">Téléphone *</label>
                <input
                  id="telephone"
                  name="telephone"
                  type="tel"
                  value={formData.telephone}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="adresseFacturation">Adresse de facturation *</label>
              <textarea
                id="adresseFacturation"
                name="adresseFacturation"
                rows={3}
                value={formData.adresseFacturation}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-section">
            <h3>Informations légales</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="siret">SIRET *</label>
                <input
                  id="siret"
                  name="siret"
                  type="text"
                  value={formData.siret}
                  onChange={handleChange}
                  pattern="[0-9]{14}"
                  maxLength={14}
                  placeholder="14 chiffres"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="siren">SIREN *</label>
                <input
                  id="siren"
                  name="siren"
                  type="text"
                  value={formData.siren}
                  onChange={handleChange}
                  pattern="[0-9]{9}"
                  maxLength={9}
                  placeholder="9 chiffres"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="tva">Numéro TVA *</label>
                <input
                  id="tva"
                  name="tva"
                  type="text"
                  value={formData.tva}
                  onChange={handleChange}
                  placeholder="FR12345678901"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="statut">Statut</label>
                <select
                  id="statut"
                  name="statut"
                  value={formData.statut}
                  onChange={handleChange}
                >
                  <option value="actif">Actif</option>
                  <option value="inactif">Inactif</option>
                  <option value="en_attente">En attente</option>
                </select>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-secondary">
              Annuler
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FicheClient;
