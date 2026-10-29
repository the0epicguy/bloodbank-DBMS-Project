/**
 * BankList.jsx  (Person 2 — converted from BankList.tsx)
 * CRUD management for Blood Banks.
 * Rewritten as plain JSX using useState/useEffect (no react-query/TypeScript).
 */
import React, { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';

const EMPTY_FORM = { name: '', address: '', city: '', contact: '', email: '' };

function BankFormModal({ initial, onSubmit, onCancel, saving }) {
  const [form, setForm] = useState(initial ? { ...initial } : { ...EMPTY_FORM });
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">
            {initial?.bank_id ? 'Edit Blood Bank' : 'Register New Blood Bank'}
          </h2>
        </div>
        <form
          className="modal-body"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(form);
          }}
        >
          {[
            { key: 'name',    label: 'Bank Name',        type: 'text',  req: true  },
            { key: 'address', label: 'Address',          type: 'text',  req: true  },
            { key: 'city',    label: 'City',             type: 'text',  req: true  },
            { key: 'contact', label: 'Contact Phone',    type: 'text',  req: true  },
            { key: 'email',   label: 'Email (optional)', type: 'email', req: false },
          ].map(({ key, label, type, req }) => (
            <div className="form-group" key={key}>
              <label className="form-label">{label}</label>
              <input
                className="form-input"
                type={type}
                value={form[key] ?? ''}
                onChange={set(key)}
                required={req}
                placeholder={`Enter ${label.toLowerCase()}`}
              />
            </div>
          ))}
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving…' : initial?.bank_id ? 'Save Changes' : 'Register Bank'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DeleteConfirmModal({ onConfirm, onCancel, saving }) {
  return (
    <div className="modal-overlay">
      <div className="modal" style={{ maxWidth: '400px', textAlign: 'center' }}>
        <div className="modal-body">
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🗑️</div>
          <h3 className="modal-title">Delete Blood Bank?</h3>
          <p className="text-secondary" style={{ margin: '0.75rem 0 1.5rem' }}>
            This permanently deletes the bank and all its blood unit records.
          </p>
          <div className="modal-actions">
            <button className="btn btn-secondary" onClick={onCancel} disabled={saving}>Cancel</button>
            <button className="btn btn-danger" onClick={onConfirm} disabled={saving}>
              {saving ? 'Deleting…' : 'Yes, Delete'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BankList() {
  const [banks, setBanks] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);       // BloodBank object or null
  const [deleteId, setDeleteId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getBanks(search ? { search } : {});
      setBanks(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Failed to load banks.');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { load(); }, [load]);

  const flash = (msg) => { setNotice(msg); setTimeout(() => setNotice(''), 3000); };

  const handleSubmit = async (form) => {
    setSaving(true);
    setError('');
    try {
      if (editing) {
        await api.updateBank(editing.bank_id, form);
        flash('Bank updated.');
      } else {
        await api.createBank(form);
        flash('Bank created.');
      }
      setShowForm(false);
      setEditing(null);
      await load();
    } catch (err) {
      setError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (deleteId === null) return;
    setSaving(true);
    try {
      await api.deleteBank(deleteId);
      setDeleteId(null);
      flash('Bank deleted.');
      await load();
    } catch (err) {
      setError(err.message || 'Delete failed.');
      setDeleteId(null);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Blood Banks</h1>
          <p className="page-subtitle">
            {banks.length} bank{banks.length !== 1 ? 's' : ''} registered
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => { setEditing(null); setShowForm(true); }}
        >
          + Register Bank
        </button>
      </div>

      {notice && <div className="alert alert-success">{notice}</div>}
      {error  && <div className="alert alert-error">{error}</div>}

      {/* Search */}
      <div className="filters-row">
        <input
          className="form-input search-input"
          placeholder="Search by name or city…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="empty-state"><div className="empty-state-text">Loading…</div></div>
      ) : banks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏥</div>
          <div className="empty-state-text">No blood banks found.</div>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>City</th>
                <th>Contact</th>
                <th className="text-center">Available Units</th>
                <th className="text-center">Expiring Soon</th>
                <th className="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {banks.map((bank) => (
                <tr key={bank.bank_id}>
                  <td>
                    <div className="font-medium">{bank.name}</div>
                    <div className="text-secondary text-sm">{bank.address}</div>
                  </td>
                  <td>{bank.city}</td>
                  <td>{bank.contact}</td>
                  <td className="text-center">
                    <span className="badge badge-success">{bank.available_units ?? 0}</span>
                  </td>
                  <td className="text-center">
                    {(bank.expiring_soon ?? 0) > 0 ? (
                      <span className="badge badge-warning">{bank.expiring_soon}</span>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="text-center">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => { setEditing(bank); setShowForm(true); }}
                    >
                      Edit
                    </button>{' '}
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => setDeleteId(bank.bank_id)}
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

      {/* Modals */}
      {showForm && (
        <BankFormModal
          initial={editing}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditing(null); }}
          saving={saving}
        />
      )}
      {deleteId !== null && (
        <DeleteConfirmModal
          onConfirm={handleDelete}
          onCancel={() => setDeleteId(null)}
          saving={saving}
        />
      )}
    </div>
  );
}
