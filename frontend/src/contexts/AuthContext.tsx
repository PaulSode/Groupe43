import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authAPI } from '../api/client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Vérifier si c'est un utilisateur mock (mode test)
      const mockUser = localStorage.getItem('mockUser');
      if (mockUser) {
        try {
          const user = JSON.parse(mockUser);
          setUser(user);
          setLoading(false);
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('mockUser');
          setLoading(false);
        }
      } else {
        // Authentification normale avec le backend
        authAPI.verify(token)
          .then(user => setUser(user))
          .catch(() => {
            localStorage.removeItem('token');
            localStorage.removeItem('mockUser');
          })
          .finally(() => setLoading(false));
      }
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { user, token } = await authAPI.login(email, password);
    localStorage.setItem('token', token);
    setUser(user);
  };

  const register = async (email: string, password: string, firstName: string, lastName: string) => {
    const { user, token } = await authAPI.register(email, password, firstName, lastName);
    localStorage.setItem('token', token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('mockUser');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};