import React, { useCallback, useState } from 'react';
import './DropZone.css';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

const DropZone: React.FC<DropZoneProps> = ({ onFilesSelected, disabled }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file =>
      file.type === 'application/pdf' ||
      file.type.startsWith('image/')
    );

    if (validFiles.length > 0) {
      onFilesSelected(validFiles);
    }
  }, [onFilesSelected, disabled]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    if (e.target.files) {
      const files = Array.from(e.target.files);
      onFilesSelected(files);
    }
  }, [onFilesSelected, disabled]);

  return (
    <div
      className={`dropzone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-input"
        multiple
        accept=".pdf,image/*"
        onChange={handleFileInput}
        disabled={disabled}
        style={{ display: 'none' }}
      />
      
      <label htmlFor="file-input" className="dropzone-content">
        <div className="dropzone-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </div>
        <div className="dropzone-text">
          <p className="dropzone-title">
            Glissez-déposez vos fichiers ici
          </p>
          <p className="dropzone-subtitle">
            ou cliquez pour parcourir
          </p>
          <p className="dropzone-hint">
            Formats acceptés : PDF, JPG, PNG (max 10 Mo par fichier)
          </p>
        </div>
      </label>
    </div>
  );
};

export default DropZone;
