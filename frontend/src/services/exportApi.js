import { api } from './api';

export const exportApi = {
  governanceReport: format => api.get(`/api/exports/governance-report.${format}`, { responseType: 'blob' }),
};
