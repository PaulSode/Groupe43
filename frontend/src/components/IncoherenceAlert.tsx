import React from 'react';
import { Incoherence } from '../types';
import './IncoherenceAlert.css';

interface IncoherenceAlertProps {
  incoherences: Incoherence[];
  onResolve?: (id: string) => void;
  onFix?: (field: string, expectedValue: string, incId: string) => void;
}

const TYPE_LABELS: Record<string, string> = {
  client_mismatch: 'Différent de la fiche client',
  inter_doc_siret: 'SIRET incohérent entre documents',
  date_expired: 'Date d\'expiration dépassée',
};

const IncoherenceAlert: React.FC<IncoherenceAlertProps> = ({ incoherences, onResolve, onFix }) => {
  if (incoherences.length === 0) return null;

  const getSeverityIcon = (severity: string) => {
    if (severity === 'high') {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      );
    }
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
      </svg>
    );
  };

  return (
    <div className="incoherence-alerts">
      <div className="alerts-header">
        <h3>Incohérences détectées ({incoherences.length})</h3>
      </div>
      <div className="alerts-list">
        {incoherences.map(inc => (
          <div key={inc.id} className={`alert-item severity-${inc.severity}`}>
            <div className="alert-icon">
              {getSeverityIcon(inc.severity)}
            </div>
            <div className="alert-content">
              <div className="alert-type">{TYPE_LABELS[inc.type] || inc.type}</div>
              <div className="alert-message">{inc.message}</div>
              {(inc.expectedValue || inc.actualValue) && (
                <div className="alert-details">
                  {inc.expectedValue && (
                    <span>Fiche client : <strong>{inc.expectedValue}</strong></span>
                  )}
                  {inc.actualValue && (
                    <span>Document : <strong>{inc.actualValue}</strong></span>
                  )}
                </div>
              )}
              {inc.type === 'client_mismatch' && inc.expectedValue && onFix && (
                <button
                  className="btn-fix"
                  onClick={() => onFix(inc.field, inc.expectedValue!, inc.id)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                  Corriger avec la valeur client
                </button>
              )}
            </div>
            <div className="alert-actions">
              {onResolve && (
                <button
                  onClick={() => onResolve(inc.id)}
                  className="btn-resolve"
                  title="Marquer comme résolu"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default IncoherenceAlert;
