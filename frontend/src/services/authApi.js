import { api } from './api';
export const authApi = {
  login: ({ email, password }) => {
    const form = new URLSearchParams();
    form.append('username', email); form.append('password', password);
    return api.post('/api/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
  },
  register: (data) => api.post('/api/auth/register', {
    ...data,
    role: data.role === 'officer' ? 'CPSE_OFFICER' : String(data.role || 'CPSE_OFFICER').toUpperCase(),
  }),
  getMe: () => api.get('/api/auth/me'),
};
