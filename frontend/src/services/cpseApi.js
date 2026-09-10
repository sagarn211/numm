import { api } from './api';
export const cpseApi = {
  getAll: () => api.get('/api/cpses'),
  getById: (id) => api.get(`/api/cpses/${id}`),
  create: (data) => api.post('/api/cpses', data),
  update: (id, data) => api.put(`/api/cpses/${id}`, data),
  remove: (id) => api.delete(`/api/cpses/${id}`),
};
