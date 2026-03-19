import React, { useState, useEffect } from 'react';
import { documentsAPI } from '../api/client';

interface Props {
  docId: string;
  filename: string;
  className?: string;
}

export const DocumentFilePreview: React.FC<Props> = ({ docId, filename, className }) => {
  const [url, setUrl] = useState<string | null>(null);
  const isPdf = filename.toLowerCase().endsWith('.pdf');

  useEffect(() => {
    let objectUrl: string;
    documentsAPI.getFile(docId)
      .then(blob => {
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(err => console.error("Erreur de récupération :", err));

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [docId]);

  if (!url) return <div className={className} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Chargement...</div>;

  if (isPdf) {
    return <iframe src={`${url}#toolbar=0&navpanes=0`} title={filename} className={className} style={{ width: '100%', height: '100%', border: 'none' }} />;
  }
  return <img src={url} alt={filename} className={className} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />;
};