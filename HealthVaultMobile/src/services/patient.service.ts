import { api } from './api';

export const patientService = {
  getDashboard: () => api.get('/patient/dashboard').then(r => r.data),
  getTimeline: (filter = 'all') => api.get(`/patient/timeline?filter=${filter}`).then(r => r.data),
  getHealthId: () => api.get('/patient/health-id').then(r => r.data),
  getHealthSummary: () => api.get('/patient/health-summary').then(r => r.data),
  getLabReports: () => api.get('/patient/records/lab').then(r => r.data),
  getLabReport: (id: string) => api.get(`/patient/records/lab/${id}`).then(r => r.data),
  getMedications: () => api.get('/patient/medications').then(r => r.data),
  getConditions: () => api.get('/patient/conditions').then(r => r.data),
  getAllergies: () => api.get('/patient/allergies').then(r => r.data),
  getVaccinations: () => api.get('/patient/vaccinations').then(r => r.data),
  getProcedures: () => api.get('/patient/procedures').then(r => r.data),
  getNotifications: () => api.get('/patient/notifications').then(r => r.data),
  getAccessHistory: () => api.get('/patient/access-history').then(r => r.data),
  getSettings: () => api.get('/patient/settings').then(r => r.data),
  updateSettings: (data: Record<string, unknown>) => api.patch('/patient/settings', data).then(r => r.data),
  getConsentRequests: () => api.get('/consent/requests').then(r => r.data),
  approveConsent: (id: string, categories: string[]) =>
    api.post(`/consent/approve/${id}`, { approved_categories: categories }).then(r => r.data),
  denyConsent: (id: string) => api.post(`/consent/deny/${id}`).then(r => r.data),
  revokeConsent: (id: string) => api.post(`/consent/revoke/${id}`).then(r => r.data),
  getDocuments: (type = 'all') => api.get(`/documents/?type=${type}`).then(r => r.data),
  deleteDocument: (id: string) => api.delete(`/documents/${id}`).then(r => r.data),
};
