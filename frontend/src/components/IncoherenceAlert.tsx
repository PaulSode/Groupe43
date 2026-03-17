import React from 'react';
import { Incoherence } from '../types';
import './IncoherenceAlert.css';

interface IncoherenceAlertProps {
  incoherences: Incoherence[];
  onResolve?: (id: string) => void;
}

const IncoherenceAlert: React.FC<IncoherenceAlertProps> = ({ incoherences, onResolve }) => {
  if (incoherences.length === 0) {
    return null;
  }

  const getSeverityClass = (severity: Incoherence['severity']) => {
    return `severity-${severity}`;
  };

  const getSeverityIcon = (severity: Incoherence['severity']) => {
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

  const getTypeLabel = (type: Incoherence['type']) => {
    const labels: Record<Incoherence['type'], string> = {
      siret_mismatch: 'SIRET incohérent',
      date_expired: 'Date expirée',
      tva_invalid: 'TVA invalide',
      iban_invalid: 'IBAN invalide',
      montant_incoherent: 'Montant incohérent',
    };
    return labels[type];
  };

  return (
    <div className="incoherence-alerts">
      <div className="alerts-header">
        <h3>Incohérences détectées ({incoherences.length})</h3>
      </div>
      <div className="alerts-list">
        {incoherences.map(inc => (
          <div key={inc.id} className={`alert-item ${getSeverityClass(inc.severity)}`}>
            <div className="alert-icon">
              {getSeverityIcon(inc.severity)}
            </div>
            <div className="alert-content">
              <div className="alert-type">{getTypeLabel(inc.type)}</div>
              <div className="alert-message">{inc.message}</div>
              {(inc.expectedValue || inc.actualValue) && (
                <div className="alert-details">
                  {inc.expectedValue && (
                    <span>Attendu : <strong>{inc.expectedValue}</strong></span>
                  )}
                  {inc.actualValue && (
                    <span>Trouvé : <strong>{inc.actualValue}</strong></span>
                  )}
                </div>
              )}
            </div>
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
        ))}
      </div>
    </div>
  );
};

export default IncoherenceAlert;
