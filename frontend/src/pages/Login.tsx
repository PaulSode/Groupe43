import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

interface LoginProps {
  onSwitchToRegister: () => void;
}

const Login: React.FC<LoginProps> = ({ onSwitchToRegister }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Identifiants invalides');
    } finally {
      setLoading(false);
    }
  };

  const handleTestLogin = () => {
    // Connexion de test sans backend
    const mockUser = {
      id: 'test-user-123',
      email: 'test@docflow.com',
      firstName: 'Jean',
      lastName: 'Dupont',
      role: 'admin' as const,
    };
    const mockToken = 'mock-jwt-token-for-testing';
    
    localStorage.setItem('token', mockToken);
    localStorage.setItem('mockUser', JSON.stringify(mockUser));
    
    // Force le rechargement de la page pour que AuthContext détecte le token
    window.location.reload();
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>DocFlow</h1>
          <p>Connexion à votre espace</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Adresse e-mail</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="votre@email.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>

          <button type="button" onClick={handleTestLogin} className="btn-test">
            Mode Test
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Pas encore de compte ?{' '}
            <button onClick={onSwitchToRegister} className="link-button">
              Créer un compte
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;