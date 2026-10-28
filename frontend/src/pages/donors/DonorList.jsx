import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';

/**
 * DonorList page — lists all donors with:
 *   - Search by name/phone
 *   - Filter by blood group
 *   - "Add Donor" modal
 *   - Click a row to see detail
 */

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function DonorList() {
  const navigate = useNavigate();

  // State
  const [donors, setDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [groupFilter, setGroupFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState(null);

  // Form state for "Add Donor"
  const [form, setForm] = useState({
    name: '',
    blood_group: 'A+',
    phone: '',
    dob: '',
  });
  const [formError, setFormError] = useState('');

  // Fetch donors
  const fetchDonors = async () => {
    setLoading(true);
    try {
      const data = await api.getDonors({
        blood_group: groupFilter || undefined,
        search: search || undefined,
      });
      setDonors(data);
    } catch (err) {
      showToast('Failed to load donors: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDonors();
  }, [groupFilter, search]);

  // Toast helper
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    try {
      await api.createDonor(form);
      showToast('Donor registered successfully!');
      setShowModal(false);
      setForm({ name: '', blood_group: 'A+', phone: '', dob: '' });
      fetchDonors();
    } catch (err) {
      setFormError(err.message);
    }
  };

  // Handle delete
  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete donor "${name}"?`)) return;

    try {
      await api.deleteDonor(id);
      showToast('Donor deleted');
      fetchDonors();
    } catch (err) {
      showToast('Delete failed: ' + err.message, 'error');
    }
  };

  return (
    <>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Blood Donors</h1>
          <p className="page-subtitle">
            Manage registered donors · {donors.length} total
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          ＋ Register Donor
        </button>
      </div>

      {/* Stat Cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon red">👥</div>
          <div>
            <div className="stat-value">{donors.length}</div>
            <div className="stat-label">Total Donors</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div>
            <div className="stat-value">
              {donors.filter((d) => !d.last_donation_date).length}
            </div>
            <div className="stat-label">Never Donated</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">🩸</div>
          <div>
            <div className="stat-value">
              {donors.filter((d) => d.last_donation_date).length}
            </div>
            <div className="stat-label">Have Donated</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">📋</div>
          <div>
            <div className="stat-value">
              {new Set(donors.map((d) => d.blood_group)).size}
            </div>
            <div className="stat-label">Blood Groups</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <input
          type="text"
          className="form-input"
          placeholder="🔍 Search by name or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="form-select"
          value={groupFilter}
          onChange={(e) => setGroupFilter(e.target.value)}
        >
          <option value="">All Blood Groups</option>
          {BLOOD_GROUPS.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="empty-state loading">
          <div className="empty-state-icon">⏳</div>
          <div className="empty-state-text">Loading donors...</div>
        </div>
      ) : donors.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">👥</div>
          <div className="empty-state-text">No donors found</div>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Blood Group</th>
                <th>Phone</th>
                <th>DOB</th>
                <th>Last Donation</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {donors.map((donor) => (
                <tr
                  key={donor.donor_id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/donors/${donor.donor_id}`)}
                >
                  <td>{donor.donor_id}</td>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {donor.name}
                  </td>
                  <td>
                    <span className="blood-group">{donor.blood_group}</span>
                  </td>
                  <td>{donor.phone}</td>
                  <td>{donor.dob}</td>
                  <td>
                    {donor.last_donation_date ? (
                      <span className="badge badge-blue">
                        {donor.last_donation_date}
                      </span>
                    ) : (
                      <span className="badge badge-yellow">Never</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(donor.donor_id, donor.name);
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Donor Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">Register New Donor</h2>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Enter donor's full name"
                  value={form.name}
                  onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                  }
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Blood Group</label>
                  <select
                    className="form-select"
                    value={form.blood_group}
                    onChange={(e) =>
                      setForm({ ...form, blood_group: e.target.value })
                    }
                  >
                    {BLOOD_GROUPS.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Phone Number</label>
                  <input
                    className="form-input"
                    type="tel"
                    placeholder="9876543210"
                    value={form.phone}
                    onChange={(e) =>
                      setForm({ ...form, phone: e.target.value })
                    }
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Date of Birth</label>
                <input
                  className="form-input"
                  type="date"
                  value={form.dob}
                  onChange={(e) =>
                    setForm({ ...form, dob: e.target.value })
                  }
                  required
                />
              </div>

              {formError && <div className="form-error">{formError}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Register Donor
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}
