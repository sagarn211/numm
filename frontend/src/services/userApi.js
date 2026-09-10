import { api } from './api';

export const userApi = {
  getAll: () => api.get('/api/users'),
  updateRole: (id, role, cpseId) => api.patch(`/api/users/${id}/role`, {
    role,
    cpse_id: cpseId ? Number(cpseId) : null,
  }),
};
