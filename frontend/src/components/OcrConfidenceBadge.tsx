import React from 'react';
import './OcrConfidenceBadge.css';

interface OcrConfidenceBadgeProps {
  confidence: number;
}

const OcrConfidenceBadge: React.FC<OcrConfidenceBadgeProps> = ({ confidence }) => {
  const getConfidenceClass = () => {
    if (confidence >= 90) return 'confidence-high';
    if (confidence >= 70) return 'confidence-medium';
    return 'confidence-low';
  };

  const getConfidenceLabel = () => {
    if (confidence >= 90) return 'Excellent';
    if (confidence >= 70) return 'Bon';
    return 'Faible';
  };

  return (
    <div className={`ocr-confidence-badge ${getConfidenceClass()}`}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      <span>{confidence}%</span>
      <span className="confidence-label">{getConfidenceLabel()}</span>
    </div>
  );
};

export default OcrConfidenceBadge;
