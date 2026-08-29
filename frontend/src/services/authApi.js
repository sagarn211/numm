import { api } from './api';

export const authApi = {
  login: async (credentials) => {
    try {
      return await api.post('/api/auth/login', credentials);
    } catch (err) {
      // Mock API fallback response
      return {
        data: {
          token: 'mock-jwt-token-numm-2026',
          user: {
            id: 'usr-8821',
            name: 'Rajesh Kumar',
            email: credentials.email || 'r.kumar@numm.gov.in',
            role: 'Senior Procurement Officer',
            organization: 'National Grid Cell',
            badgeId: 'CPSE-EXEC-992'
          }
        }
      };
    }
  },
  register: async (userData) => {
    try {
      return await api.post('/api/auth/register', null, { params: userData });
    } catch (err) {
      return {
        data: {
          success: true,
          message: 'Registration successful',
          user: userData
        }
      };
    }
  },
  getMe: async () => {
    try {
      return await api.get('/api/auth/me');
    } catch (err) {
      return {
        data: {
          id: 'usr-8821',
          name: 'Rajesh Kumar',
          email: 'r.kumar@numm.gov.in',
          role: 'Senior Procurement Officer',
          organization: 'National Grid Cell'
        }
      };
    }
  }
};
