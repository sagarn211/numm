import { api } from "./api";

export const userApi = {
  getAll: () => api.get("/api/users"),
  updateRole: (id, role, cpseId) =>
    api.patch(`/api/users/${id}/role`, {
      role,
      cpse_id: cpseId ? Number(cpseId) : null,
    }),
  approve: (id, role, cpseId, comment = "") =>
    api.post(`/api/users/${id}/approve`, {
      role,
      cpse_id: cpseId ? Number(cpseId) : null,
      comment,
    }),
  reject: (id, comment = "") =>
    api.post(`/api/users/${id}/reject`, { comment }),
  delete: (id) => api.delete(`/api/users/${id}`),
};
