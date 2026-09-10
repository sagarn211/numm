/* eslint-disable react-refresh/only-export-components */
import { createContext, useEffect, useState } from 'react';
import { authApi } from '../services/authApi';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('numm_user'));
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    const expire = () => {
      localStorage.removeItem('numm_user');
      setUser(null);
    };
    window.addEventListener('numm:session-expired', expire);

    const restoreSession = async () => {
      const token = localStorage.getItem('numm_token');
      if (!token) {
        localStorage.removeItem('numm_user');
        setUser(null);
        setAuthReady(true);
        return;
      }
      try {
        const response = await authApi.getMe();
        setUser(response.data);
        localStorage.setItem('numm_user', JSON.stringify(response.data));
      } catch {
        localStorage.removeItem('numm_token');
        localStorage.removeItem('numm_user');
        setUser(null);
      } finally {
        setAuthReady(true);
      }
    };

    restoreSession();
    return () => window.removeEventListener('numm:session-expired', expire);
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const response = await authApi.login({ email, password });
      const token = response.data.access_token || response.data.token;
      if (!token || !response.data.user) throw new Error('Invalid login response');
      localStorage.setItem('numm_token', token);
      localStorage.setItem('numm_user', JSON.stringify(response.data.user));
      setUser(response.data.user);
      return response.data.user;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('numm_user');
    localStorage.removeItem('numm_token');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, loading, authReady }}>
      {children}
    </AuthContext.Provider>
  );
};
