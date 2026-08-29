import React, { createContext, useState, useEffect } from 'react';
import { authApi } from '../services/authApi';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('numm_user');
    if (savedUser) {
      try { return JSON.parse(savedUser); } catch { return null; }
    }
    return null;
  });

  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const response = await authApi.login({ email, password });
      const userData = response.data.user || {
        id: 'usr-8821',
        name: 'Rajesh Kumar',
        email: email || 'r.kumar@numm.gov.in',
        role: 'Senior Procurement Officer',
        organization: 'National Grid Cell',
        badgeId: 'CPSE-EXEC-992'
      };
      setUser(userData);
      localStorage.setItem('numm_user', JSON.stringify(userData));
      if (response.data.token) {
        localStorage.setItem('numm_token', response.data.token);
      }
      return userData;
    } catch (err) {
      // Fallback for offline demo mode
      const mockUser = {
        id: 'usr-8821',
        name: 'Rajesh Kumar',
        email: email || 'r.kumar@numm.gov.in',
        role: 'Senior Procurement Officer',
        organization: 'National Grid Cell',
        badgeId: 'CPSE-EXEC-992'
      };
      setUser(mockUser);
      localStorage.setItem('numm_user', JSON.stringify(mockUser));
      return mockUser;
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
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
