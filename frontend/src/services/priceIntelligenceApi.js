import { api } from "./api";

export const priceIntelligenceApi = {
  summary: () => api.get("/api/procurement/price-intelligence/summary"),
  materials: (search = "") =>
    api.get("/api/procurement/price-intelligence/materials", {
      params: { search, limit: 25 },
    }),
  detail: (id, params = {}) =>
    api.get(`/api/procurement/price-intelligence/${id}`, { params }),
  highlights: () => api.get("/api/procurement/price-intelligence/highlights"),
};
