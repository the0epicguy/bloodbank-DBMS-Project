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

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
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
};

export default api;
