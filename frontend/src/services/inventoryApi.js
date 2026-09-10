import { api } from './api';
export const inventoryApi={getAll:(p={})=>api.get('/api/inventory',{params:p}),create:(d)=>api.post('/api/inventory',d),update:(id,d)=>api.put(`/api/inventory/${id}`,d),getAvailability:(id)=>api.get(`/api/national-materials/${id}/availability`)};
