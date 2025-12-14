import axios from 'axios';

// API URL - use environment variable or default to the API subdomain
const API_URL = import.meta.env.VITE_API_URL || 'http://api.213.199.55.191.nip.io';

const api = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Sites API
export const sitesApi = {
    list: () => api.get('/sites'),
    get: (id) => api.get(`/sites/${id}`),
    create: (data) => api.post('/sites', data),
    update: (id, data) => api.put(`/sites/${id}`, data),
    delete: (id) => api.delete(`/sites/${id}`),
    testConnection: (id) => api.post(`/sites/${id}/test-connection`),
    syncCategories: (id) => api.post(`/sites/${id}/sync-categories`),
};

// Sources API
export const sourcesApi = {
    list: (siteId = null) => api.get('/sources', { params: { site_id: siteId } }),
    get: (id) => api.get(`/sources/${id}`),
    create: (data) => api.post('/sources', data),
    update: (id, data) => api.put(`/sources/${id}`, data),
    delete: (id) => api.delete(`/sources/${id}`),
    poll: (id) => api.post(`/sources/${id}/poll`),
};

// Articles API
export const articlesApi = {
    list: (params = {}) => api.get('/articles', { params }),
    get: (id) => api.get(`/articles/${id}`),
    retry: (id) => api.post(`/articles/${id}/retry`),
    delete: (id) => api.delete(`/articles/${id}`),
    stats: (siteId = null) => api.get('/articles/stats/summary', { params: { site_id: siteId } }),
};

// Dashboard API
export const dashboardApi = {
    stats: () => api.get('/dashboard/stats'),
    recent: (limit = 10) => api.get('/dashboard/recent', { params: { limit } }),
    chart: (days = 7) => api.get('/dashboard/chart/daily', { params: { days } }),
};

export default api;
