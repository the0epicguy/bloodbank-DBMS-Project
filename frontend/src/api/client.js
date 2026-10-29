
const BASE_URL = '/api';

async function request(endpoint, options = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = error.detail;
    throw new Error(
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(', ')
          : `Request failed (${response.status})`
    );
  }

  if (response.status === 204) return null;
  return response.json();
}

function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const result = query.toString();
  return result ? `?${result}` : '';
}

const api = {
  // Donors
  getDonors: (params = {}) => request(`/donors/${queryString(params)}`),
  getDonor: (id) => request(`/donors/${id}`),
  createDonor: (data) => request('/donors/', { method: 'POST', body: JSON.stringify(data) }),
  updateDonor: (id, data) => request(`/donors/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDonor: (id) => request(`/donors/${id}`, { method: 'DELETE' }),
  checkEligibility: (id) => request(`/donors/${id}/eligibility`),
  getDonationHistory: (id) => request(`/donors/${id}/history`),
  recordDonation: (data) => request('/donations/', { method: 'POST', body: JSON.stringify(data) }),

  // Hospitals
  getHospitals: (params = {}) => request(`/hospitals/${queryString(params)}`),
  createHospital: (data) => request('/hospitals/', { method: 'POST', body: JSON.stringify(data) }),
  updateHospital: (id, data) => request(`/hospitals/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteHospital: (id) => request(`/hospitals/${id}`, { method: 'DELETE' }),

  // Recipients
  getRecipients: (params = {}) => request(`/recipients/${queryString(params)}`),
  createRecipient: (data) => request('/recipients/', { method: 'POST', body: JSON.stringify(data) }),
  updateRecipient: (id, data) => request(`/recipients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRecipient: (id) => request(`/recipients/${id}`, { method: 'DELETE' }),

  // Blood requests
  getRequests: (params = {}) => request(`/requests/${queryString(params)}`),
  createRequest: (data) => request('/requests/', { method: 'POST', body: JSON.stringify(data) }),
  cancelRequest: (id) => request(`/requests/${id}/cancel`, { method: 'PATCH' }),
};

export default api;
