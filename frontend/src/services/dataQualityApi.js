import { api } from './api';
export const dataQualityApi={getMetrics:()=>api.get('/api/data-quality')};
