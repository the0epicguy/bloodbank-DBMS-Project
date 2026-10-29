/**
 * API Client for the Blood Bank backend.
 *
 * All API calls go through this module.
 * The Vite dev server proxies /api/* to http://localhost:8000/*
 *
 * Usage:
 *   import api from './api/client';
 *   const donors = await api.getDonors();
 */

const BASE_URL = '/api';

// ---- Auth token storage (Person 4) ----
const TOKEN_KEY = 'bloodbank_token';
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  const token = getToken();
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    // Expired / invalid session -> tell the app to show the login page
    if (response.status === 401 && token) {
      clearToken();
      window.dispatchEvent(new Event('auth:logout'));
    }
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = Array.isArray(error.detail)
      ? error.detail.map((d) => d.msg).join(', ')   // FastAPI validation errors
      : error.detail;
    throw new Error(detail || `HTTP ${response.status}`);
  }

  // 204 No Content (e.g. DELETE)
  if (response.status === 204) return null;

  return response.json();
}

const api = {
  // ---- Donors ----
  getDonors: (params = {}) => {
    const query = new URLSearchParams();
    if (params.blood_group) query.set('blood_group', params.blood_group);
    if (params.search) query.set('search', params.search);
    if (params.skip) query.set('skip', params.skip);
    if (params.limit) query.set('limit', params.limit);
    const qs = query.toString();
    return request(`/donors/${qs ? '?' + qs : ''}`);
  },

  getDonor: (id) => request(`/donors/${id}`),

  createDonor: (data) =>
    request('/donors/', { method: 'POST', body: JSON.stringify(data) }),

  updateDonor: (id, data) =>
    request(`/donors/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteDonor: (id) =>
    request(`/donors/${id}`, { method: 'DELETE' }),

  checkEligibility: (id) => request(`/donors/${id}/eligibility`),

  getDonationHistory: (id) => request(`/donors/${id}/history`),

  // ---- Donations ----
  recordDonation: (data) =>
    request('/donations/', { method: 'POST', body: JSON.stringify(data) }),

  // ---- Auth (Person 4) ----
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  demoLogin: (role) => request(`/auth/demo-login/${role}`, { method: 'POST' }),
  getMe: () => request('/auth/me'),

  // ---- Issues (Person 4) ----
  getIssues: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.set(k, v);
    });
    const qs = query.toString();
    return request(`/issues/${qs ? '?' + qs : ''}`);
  },
  getPendingRequests: () => request('/issues/pending-requests'),
  getFefoPreview: (requestId) => request(`/requests/${requestId}/fefo-preview`),
  autoFulfil: (requestId) =>
    request(`/requests/${requestId}/auto-fulfil`, { method: 'POST' }),
  manualIssue: (data) =>
    request('/issues/manual', { method: 'POST', body: JSON.stringify(data) }),

  // ---- Reports (Person 4) ----
  getSummary: () => request('/reports/summary'),
  getStockDistribution: () => request('/reports/stock-distribution'),
  getExpiringSoon: () => request('/reports/expiring-soon'),
  getFulfillmentMetrics: () => request('/reports/fulfillment-metrics'),
};

export default api;
