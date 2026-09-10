import { api } from './api';
export const integrationApi={syncSap:(cpse_id,connector='MOCK')=>api.post('/api/integrations/sap/sync',{cpse_id,connector}),pushMappings:(cpse_id,connector='ODATA')=>api.post('/api/integrations/sap/push-mappings',{cpse_id,connector}),getSapStatus:()=>api.get('/api/integrations/sap/status'),getSapHistory:()=>api.get('/api/integrations/sap/history')};
