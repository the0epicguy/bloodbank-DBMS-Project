import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api/client';

/**
 * DonorDetail page — shows:
 *   - Donor info card
 *   - Eligibility check
 *   - Donation history
 *   - "Record Donation" modal
 */

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function DonorDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [donor, setDonor] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDonateModal, setShowDonateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [toast, setToast] = useState(null);

  // Donation form
  const [donateForm, setDonateForm] = useState({
    bank_id: 1,
    volume_ml: 450,
    component_type: 'WHOLE_BLOOD',
  });
  const [donateError, setDonateError] = useState('');

  // Edit form
  const [editForm, setEditForm] = useState({
    name: '',
    blood_group: '',
    phone: '',
    dob: '',
  });
  const [editError, setEditError] = useState('');

  const showToast = (msg, type = 'success') => {
    setToast({ message: msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [d, e, h] = await Promise.all([
        api.getDonor(id),
        api.checkEligibility(id),
        api.getDonationHistory(id),
      ]);
      setDonor(d);
      setEligibility(e);
      setHistory(h);
      setEditForm({
        name: d.name,
        blood_group: d.blood_group,
        phone: d.phone,
        dob: d.dob,
      });
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [id]);

  const handleDonate = async (e) => {
    e.preventDefault();
    setDonateError('');
    try {
      await api.recordDonation({ donor_id: parseInt(id), ...donateForm });
      showToast('Donation recorded successfully!');
      setShowDonateModal(false);
      fetchAll();
    } catch (err) {
      setDonateError(err.message);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    setEditError('');
    try {
      await api.updateDonor(id, editForm);
      showToast('Donor updated successfully!');
      setShowEditModal(false);
      fetchAll();
    } catch (err) {
      setEditError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="empty-state loading">
        <div className="empty-state-icon">⏳</div>
        <div className="empty-state-text">Loading donor details...</div>
      </div>
    );
  }

  if (!donor) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">❌</div>
        <div className="empty-state-text">Donor not found</div>
      </div>
    );
  }

  return (
    <>
      {/* Back button */}
      <button
        className="btn btn-secondary"
        onClick={() => navigate('/')}
        style={{ marginBottom: 'var(--space-6)' }}
      >
        ← Back to List
      </button>

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">{donor.name}</h1>
          <p className="page-subtitle">Donor ID: {donor.donor_id}</p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button className="btn btn-secondary" onClick={() => setShowEditModal(true)}>
            ✏️ Edit
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setShowDonateModal(true)}
          >
            🩸 Record Donation
          </button>
        </div>
      </div>

      {/* Donor Info + Eligibility Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        {/* Info Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Donor Information</h3>
            <span className="blood-group" style={{ fontSize: '1.2rem', padding: '0.5rem 1rem' }}>
              {donor.blood_group}
            </span>
          </div>
          <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>Phone</span>
              <div>{donor.phone}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>Date of Birth</span>
              <div>{donor.dob}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>Last Donation</span>
              <div>
                {donor.last_donation_date ? (
                  <span className="badge badge-blue">{donor.last_donation_date}</span>
                ) : (
                  <span className="badge badge-yellow">Never donated</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Eligibility Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Eligibility Status</h3>
          </div>
          {eligibility && (
            <div style={{ textAlign: 'center', padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>
                {eligibility.is_eligible ? '✅' : '❌'}
              </div>
              <div
                className={`badge ${eligibility.is_eligible ? 'badge-green' : 'badge-red'}`}
                style={{ fontSize: 'var(--font-size-base)', padding: '0.5rem 1rem' }}
              >
                {eligibility.is_eligible ? 'ELIGIBLE' : 'NOT ELIGIBLE'}
              </div>
              <p
                style={{
                  marginTop: 'var(--space-4)',
                  color: 'var(--text-secondary)',
                  fontSize: 'var(--font-size-sm)',
                }}
              >
                {eligibility.reason}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Donation History */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Donation History</h3>
          <span className="badge badge-blue">{history.length} donations</span>
        </div>

        {history.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-text">No donations recorded yet</div>
          </div>
        ) : (
          <div className="table-container" style={{ border: 'none' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Bank ID</th>
                  <th>Unit ID</th>
                  <th>Date</th>
                  <th>Volume (ml)</th>
                  <th>Component</th>
                  <th>Blood Group</th>
                  <th>Expiry</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((unit, i) => (
                  <tr key={i}>
                    <td>{unit.bank_id}</td>
                    <td>{unit.unit_id}</td>
                    <td>{unit.donation_date}</td>
                    <td>{unit.volume_ml}</td>
                    <td>
                      <span className="badge badge-blue">
                        {unit.component_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <span className="blood-group">{unit.blood_group}</span>
                    </td>
                    <td>{unit.expiry_date}</td>
                    <td>
                      <span
                        className={`badge ${
                          unit.status === 'AVAILABLE'
                            ? 'badge-green'
                            : unit.status === 'ISSUED'
                            ? 'badge-blue'
                            : unit.status === 'EXPIRED'
                            ? 'badge-red'
                            : 'badge-yellow'
                        }`}
                      >
                        {unit.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Record Donation Modal */}
      {showDonateModal && (
        <div className="modal-overlay" onClick={() => setShowDonateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">🩸 Record Donation</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-6)', fontSize: 'var(--font-size-sm)' }}>
              Recording donation for <strong>{donor.name}</strong> ({donor.blood_group})
            </p>

            <form onSubmit={handleDonate}>
              <div className="form-group">
                <label className="form-label">Blood Bank ID</label>
                <input
                  className="form-input"
                  type="number"
                  min="1"
                  value={donateForm.bank_id}
                  onChange={(e) =>
                    setDonateForm({ ...donateForm, bank_id: parseInt(e.target.value) })
                  }
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Volume (ml)</label>
                  <input
                    className="form-input"
                    type="number"
                    min="50"
                    max="600"
                    value={donateForm.volume_ml}
                    onChange={(e) =>
                      setDonateForm({
                        ...donateForm,
                        volume_ml: parseInt(e.target.value),
                      })
                    }
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Component Type</label>
                  <select
                    className="form-select"
                    value={donateForm.component_type}
                    onChange={(e) =>
                      setDonateForm({
                        ...donateForm,
                        component_type: e.target.value,
                      })
                    }
                  >
                    <option value="WHOLE_BLOOD">Whole Blood</option>
                    <option value="RBC">RBC</option>
                    <option value="PLATELETS">Platelets</option>
                    <option value="PLASMA">Plasma</option>
                  </select>
                </div>
              </div>

              {donateError && <div className="form-error">{donateError}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowDonateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Record Donation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Donor Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">✏️ Edit Donor</h2>

            <form onSubmit={handleEdit}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  className="form-input"
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Blood Group</label>
                  <select
                    className="form-select"
                    value={editForm.blood_group}
                    onChange={(e) =>
                      setEditForm({ ...editForm, blood_group: e.target.value })
                    }
                  >
                    {BLOOD_GROUPS.map((g) => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Phone</label>
                  <input
                    className="form-input"
                    type="tel"
                    value={editForm.phone}
                    onChange={(e) =>
                      setEditForm({ ...editForm, phone: e.target.value })
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
                  value={editForm.dob}
                  onChange={(e) =>
                    setEditForm({ ...editForm, dob: e.target.value })
                  }
                  required
                />
              </div>

              {editError && <div className="form-error">{editError}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowEditModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}
