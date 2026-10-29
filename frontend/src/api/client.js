/**
 * Unified API Client for the Blood Bank backend.
 *
 * All API calls from all persons go through this module.
 * The Vite dev server proxies /api/* to http://localhost:8000/*
 *
 * Sections:
 *   Auth (P4)           – login, demo-login, me
 *   Donors (P1)         – CRUD + eligibility + history
 *   Donations (P1)      – record a donation
 *   Blood Banks (P2)    – CRUD banks
 *   Inventory (P2)      – stock summary, expiry sweep
 *   Hospitals (P3)      – CRUD hospitals
 *   Recipients (P3)     – CRUD recipients
 *   Requests (P3)       – CRUD blood requests + cancel
 *   Issues (P4)         – issue log, FEFO auto-fulfil, manual issue
 *   Reports (P4)        – dashboard metrics
 */

const BASE_URL = '/api';

// ── Auth token storage ─────────────────────────────────────────────────────
const TOKEN_KEY = 'bloodbank_token';
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

// ── Core fetch helper ──────────────────────────────────────────────────────
function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') query.set(k, v);
  });
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

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
    // Expired / invalid session → broadcast logout
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

  if (response.status === 204) return null;  // 204 No Content (DELETE)
  return response.json();
}

const api = {
  // ── Auth (Person 4) ───────────────────────────────────────────────────────
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  demoLogin: (role) => request(`/auth/demo-login/${role}`, { method: 'POST' }),
  getMe: () => request('/auth/me'),

  // ── Donors (Person 1) ─────────────────────────────────────────────────────
  getDonors: (params = {}) => request(`/donors/${queryString(params)}`),
  getDonor: (id) => request(`/donors/${id}`),
  createDonor: (data) =>
    request('/donors/', { method: 'POST', body: JSON.stringify(data) }),
  updateDonor: (id, data) =>
    request(`/donors/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDonor: (id) => request(`/donors/${id}`, { method: 'DELETE' }),
  checkEligibility: (id) => request(`/donors/${id}/eligibility`),
  getDonationHistory: (id) => request(`/donors/${id}/history`),

  // ── Donations (Person 1) ──────────────────────────────────────────────────
  recordDonation: (data) =>
    request('/donations/', { method: 'POST', body: JSON.stringify(data) }),

  // ── Blood Banks (Person 2) ────────────────────────────────────────────────
  getBanks: (params = {}) => request(`/banks/${queryString(params)}`),
  getBank: (id) => request(`/banks/${id}`),
  createBank: (data) =>
    request('/banks/', { method: 'POST', body: JSON.stringify(data) }),
  updateBank: (id, data) =>
    request(`/banks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteBank: (id) => request(`/banks/${id}`, { method: 'DELETE' }),

  // ── Inventory (Person 2) ──────────────────────────────────────────────────
  // /inventory/summary?bank_id=X  – returns { banks, total_available, low_stock_alerts }
  // same endpoint serves both "per bank" and "global" depending on bank_id param
  getInventorySummary: (bankId) =>
    request(`/inventory/summary${bankId ? `?bank_id=${bankId}` : ''}`),
  getGlobalSummary: () => request('/inventory/summary'),
  // /inventory/expire-sweep  (POST)
  runExpirySweep: () => request('/inventory/expire-sweep', { method: 'POST' }),

  // ── Hospitals (Person 3) ──────────────────────────────────────────────────
  getHospitals: (params = {}) => request(`/hospitals/${queryString(params)}`),
  createHospital: (data) =>
    request('/hospitals/', { method: 'POST', body: JSON.stringify(data) }),
  updateHospital: (id, data) =>
    request(`/hospitals/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteHospital: (id) => request(`/hospitals/${id}`, { method: 'DELETE' }),

  // ── Recipients (Person 3) ─────────────────────────────────────────────────
  getRecipients: (params = {}) => request(`/recipients/${queryString(params)}`),
  createRecipient: (data) =>
    request('/recipients/', { method: 'POST', body: JSON.stringify(data) }),
  updateRecipient: (id, data) =>
    request(`/recipients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRecipient: (id) => request(`/recipients/${id}`, { method: 'DELETE' }),

  // ── Blood Requests (Person 3) ─────────────────────────────────────────────
  getRequests: (params = {}) => request(`/requests/${queryString(params)}`),
  createRequest: (data) =>
    request('/requests/', { method: 'POST', body: JSON.stringify(data) }),
  cancelRequest: (id) =>
    request(`/requests/${id}/cancel`, { method: 'PATCH' }),

  // ── Issues / Fulfilment (Person 4) ────────────────────────────────────────
  getIssues: (params = {}) => request(`/issues/${queryString(params)}`),
  getPendingRequests: () => request('/issues/pending-requests'),
  getFefoPreview: (requestId) => request(`/requests/${requestId}/fefo-preview`),
  autoFulfil: (requestId) =>
    request(`/requests/${requestId}/auto-fulfil`, { method: 'POST' }),
  manualIssue: (data) =>
    request('/issues/manual', { method: 'POST', body: JSON.stringify(data) }),

  // ── Reports / Dashboard (Person 4) ───────────────────────────────────────
  getSummary: () => request('/reports/summary'),
  getStockDistribution: () => request('/reports/stock-distribution'),
  getExpiringSoon: () => request('/reports/expiring-soon'),
  getFulfillmentMetrics: () => request('/reports/fulfillment-metrics'),
};

export default api;
