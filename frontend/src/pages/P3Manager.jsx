
import React, { useCallback, useEffect, useState } from 'react';
import api from '../api/client';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const COMPONENTS = ['WHOLE_BLOOD', 'RBC', 'PLATELETS', 'PLASMA'];
const URGENCIES = ['ROUTINE', 'URGENT', 'EMERGENCY'];
const STATUSES = ['PENDING', 'PARTIALLY_FULFILLED', 'FULFILLED', 'CANCELLED'];

const CONFIG = {
  hospitals: {
    title: 'Hospitals',
    description: 'Manage hospitals connected to your blood bank.',
    singular: 'Hospital',
    columns: ['ID', 'Hospital name', 'Address', 'Contact'],
  },
  recipients: {
    title: 'Recipients',
    description: 'Maintain recipient details and blood group records.',
    singular: 'Recipient',
    columns: ['ID', 'Recipient name', 'Age', 'Blood group'],
  },
  requests: {
    title: 'Blood requests',
    description: 'Monitor requests, urgency and fulfilment status.',
    singular: 'Request',
    columns: ['Request', 'Hospital', 'Recipient', 'Component', 'Quantity', 'Urgency', 'Status', 'Date'],
  },
};

const initialForms = {
  hospitals: { name: '', address: '', contact: '' },
  recipients: { name: '', age: '', blood_group: 'O+' },
  requests: {
    hospital_id: '',
    recipient_id: '',
    component_type: 'WHOLE_BLOOD',
    quantity: 1,
    urgency: 'ROUTINE',
  },
};

const toList = (result) => Array.isArray(result) ? result : [];

const readable = (value) =>
  String(value ?? '').replaceAll('_', ' ').toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

function Badge({ value }) {
  const normalized = String(value || '').toLowerCase().replaceAll('_', '-');
  return <span className={`badge badge-${normalized}`}>{readable(value) || 'Unknown'}</span>;
}

export default function P3Manager({ type }) {
  const config = CONFIG[type];

  const [items, setItems] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [hospitals, setHospitals] = useState([]);
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...initialForms[type] });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const params = type === 'hospitals'
        ? { search: search || undefined }
        : type === 'recipients'
          ? { search: search || undefined, blood_group: filter || undefined }
          : { status: filter || undefined };

      const result = toList(
        type === 'hospitals'
          ? await api.getHospitals(params)
          : type === 'recipients'
            ? await api.getRecipients(params)
            : await api.getRequests(params)
      );

      setItems(result);

      // Fetch unfiltered records for accurate totals.
      try {
        const all = toList(
          type === 'hospitals'
            ? await api.getHospitals()
            : type === 'recipients'
              ? await api.getRecipients()
              : await api.getRequests()
        );
        setTotalCount(all.length);
      } catch {
        setTotalCount(result.length);
      }
    } catch (err) {
      setError(err.message || 'Unable to load records.');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [type, search, filter]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (type !== 'requests') return;

    Promise.allSettled([api.getHospitals(), api.getRecipients()])
      .then(([h, r]) => {
        if (h.status === 'fulfilled') setHospitals(toList(h.value));
        if (r.status === 'fulfilled') setRecipients(toList(r.value));
      });
  }, [type]);

  const openForm = (item = null) => {
    setEditing(item);
    setError('');
    setNotice('');

    if (!item) {
      setForm({ ...initialForms[type] });
    } else if (type === 'hospitals') {
      setForm({
        name: item.name || '',
        address: item.address || '',
        contact: item.contact || '',
      });
    } else {
      setForm({
        name: item.name || '',
        age: item.age ?? '',
        blood_group: item.blood_group || 'O+',
      });
    }

    setShowForm(true);
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');

    try {
      if (type === 'hospitals') {
        const data = {
          name: form.name.trim(),
          address: form.address.trim(),
          contact: form.contact.trim(),
        };

        if (editing) {
          await api.updateHospital(editing.hospital_id, data);
        } else {
          await api.createHospital(data);
        }
      } else if (type === 'recipients') {
        const data = {
          name: form.name.trim(),
          age: form.age === '' ? null : Number(form.age),
          blood_group: form.blood_group,
        };

        if (editing) {
          await api.updateRecipient(editing.recipient_id, data);
        } else {
          await api.createRecipient(data);
        }
      } else {
        await api.createRequest({
          ...form,
          hospital_id: Number(form.hospital_id),
          recipient_id: Number(form.recipient_id),
          quantity: Number(form.quantity),
        });
      }

      setShowForm(false);
      setEditing(null);
      setNotice(`${config.singular} ${editing ? 'updated' : 'created'} successfully.`);
      await load();
    } catch (err) {
      setError(err.message || 'Unable to save this record.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (item) => {
    const id = item.hospital_id ?? item.recipient_id;
    const name = item.name || `${config.singular} #${id}`;

    if (!window.confirm(`Delete ${name}? This action cannot be undone.`)) return;

    setError('');
    setNotice('');

    try {
      if (type === 'hospitals') await api.deleteHospital(id);
      else await api.deleteRecipient(id);

      setNotice(`${config.singular} deleted successfully.`);
      await load();
    } catch (err) {
      setError(err.message || 'Unable to delete this record.');
    }
  };

  const cancelRequest = async (item) => {
    if (!window.confirm(`Cancel request REQ-${item.request_id}?`)) return;

    setError('');
    setNotice('');

    try {
      await api.cancelRequest(item.request_id);
      setNotice(`Request REQ-${item.request_id} cancelled.`);
      await load();
    } catch (err) {
      setError(err.message || 'Unable to cancel this request.');
    }
  };

  if (!config) return <div className="inline-alert error-alert">Unknown module.</div>;

  const pendingCount = items.filter(
    (item) => item.status === 'PENDING' || item.status === 'PARTIALLY_FULFILLED'
  ).length;

  const emergencyCount = items.filter(
    (item) =>
      item.urgency === 'EMERGENCY' &&
      !['CANCELLED', 'FULFILLED'].includes(item.status)
  ).length;

  const formatDate = (value) => {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? value
      : date.toLocaleDateString('en-IN', {
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        });
  };

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            {type === 'requests' ? 'REQUEST MANAGEMENT' : 'DIRECTORY MANAGEMENT'}
          </div>
          <h1 className="page-title">{config.title}</h1>
          <p className="page-subtitle">{config.description}</p>
        </div>

        <button className="btn btn-primary" onClick={() => openForm()}>
          + {type === 'requests' ? 'New request' : `Add ${config.singular}`}
        </button>
      </div>

      <div className="stat-grid compact-stats">
        <div className="stat-card">
          <div className="stat-icon red">
            {type === 'hospitals' ? 'H' : type === 'recipients' ? 'R' : 'B'}
          </div>
          <div>
            <div className="stat-label">Total records</div>
            <div className="stat-value">{totalCount}</div>
          </div>
        </div>

        {type === 'requests' && (
          <>
            <div className="stat-card">
              <div className="stat-icon amber">!</div>
              <div>
                <div className="stat-label">Pending in view</div>
                <div className="stat-value">{pendingCount}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon blue">E</div>
              <div>
                <div className="stat-label">Active emergencies in view</div>
                <div className="stat-value">{emergencyCount}</div>
              </div>
            </div>
          </>
        )}
      </div>

      <section className="card management-card">
        <div className="filters-bar management-filters">
          {type !== 'requests' && (
            <input
              className="form-input search-input"
              placeholder={`Search ${config.title.toLowerCase()}...`}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          )}

          {type === 'recipients' && (
            <select
              className="form-select"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="">All blood groups</option>
              {BLOOD_GROUPS.map((group) => (
                <option key={group} value={group}>{group}</option>
              ))}
            </select>
          )}

          {type === 'requests' && (
            <select
              className="form-select"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="">All statuses</option>
              {STATUSES.map((status) => (
                <option key={status} value={status}>{readable(status)}</option>
              ))}
            </select>
          )}

          <button className="btn btn-secondary" onClick={load} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <span className="result-count">
            Showing {items.length} of {totalCount}
          </span>
        </div>

        {error && <div className="inline-alert error-alert">{error}</div>}
        {notice && <div className="inline-alert success-alert">{notice}</div>}

        {loading ? (
          <div className="empty-state">Loading {config.title.toLowerCase()}...</div>
        ) : error && items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-text">Unable to load records</div>
            <p className="muted-text">Check your connection and try refreshing.</p>
            <button className="btn btn-secondary" onClick={load}>Try again</button>
          </div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-illustration">+</div>
            <div className="empty-state-text">No {config.title.toLowerCase()} found</div>
            <p className="muted-text">
              {type === 'requests'
                ? 'Create a blood request to get started.'
                : 'Try another search or add a new record.'}
            </p>
            {type !== 'requests' && (
              <button className="btn btn-primary" onClick={() => openForm()}>
                Add {config.singular}
              </button>
            )}
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  {config.columns.map((column) => <th key={column}>{column}</th>)}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const id = item.hospital_id ?? item.recipient_id ?? item.request_id;

                  return (
                    <tr key={id}>
                      {type === 'hospitals' && (
                        <>
                          <td>#{item.hospital_id}</td>
                          <td className="primary-cell">{item.name}</td>
                          <td>{item.address || 'Not provided'}</td>
                          <td>{item.contact || 'Not provided'}</td>
                        </>
                      )}

                      {type === 'recipients' && (
                        <>
                          <td>#{item.recipient_id}</td>
                          <td className="primary-cell">{item.name}</td>
                          <td>{item.age ?? 'Not provided'}</td>
                          <td><span className="blood-group">{item.blood_group}</span></td>
                        </>
                      )}

                      {type === 'requests' && (
                        <>
                          <td className="primary-cell">REQ-{item.request_id}</td>
                          <td>{item.hospital?.name || `Hospital #${item.hospital_id}`}</td>
                          <td>{item.recipient?.name || `Recipient #${item.recipient_id}`}</td>
                          <td>{readable(item.component_type)}</td>
                          <td>{item.quantity}</td>
                          <td><Badge value={item.urgency} /></td>
                          <td><Badge value={item.status} /></td>
                          <td>{formatDate(item.request_date)}</td>
                        </>
                      )}

                      <td>
                        {type === 'requests' ? (
                          !['CANCELLED', 'FULFILLED'].includes(item.status) ? (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => cancelRequest(item)}
                            >
                              Cancel
                            </button>
                          ) : <span className="muted-text">No action</span>
                        ) : (
                          <div className="action-buttons">
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => openForm(item)}
                            >
                              Edit
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => remove(item)}
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {showForm && (
        <div className="modal-overlay" onClick={() => !saving && setShowForm(false)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <div className="modal-heading">
              <div className="eyebrow">{editing ? 'EDIT RECORD' : 'NEW RECORD'}</div>
              <h2 className="modal-title">
                {type === 'requests'
                  ? 'Create blood request'
                  : `${editing ? 'Edit' : 'Add'} ${config.singular.toLowerCase()}`}
              </h2>
              <p className="muted-text">Enter the details below to continue.</p>
            </div>

            <form onSubmit={submit}>
              {(type === 'hospitals' || type === 'recipients') && (
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input
                    className="form-input"
                    maxLength={100}
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                    required
                  />
                </div>
              )}

              {type === 'hospitals' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Address</label>
                    <textarea
                      className="form-input"
                      rows="3"
                      value={form.address}
                      onChange={(event) => setForm({ ...form, address: event.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Contact number</label>
                    <input
                      className="form-input"
                      maxLength={20}
                      value={form.contact}
                      onChange={(event) => setForm({ ...form, contact: event.target.value })}
                      required
                    />
                  </div>
                </>
              )}

              {type === 'recipients' && (
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Age</label>
                    <input
                      className="form-input"
                      type="number"
                      min="0"
                      max="120"
                      value={form.age}
                      onChange={(event) => setForm({ ...form, age: event.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Blood group</label>
                    <select
                      className="form-select"
                      value={form.blood_group}
                      onChange={(event) => setForm({ ...form, blood_group: event.target.value })}
                    >
                      {BLOOD_GROUPS.map((group) => (
                        <option key={group} value={group}>{group}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {type === 'requests' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Hospital</label>
                    <select
                      className="form-select"
                      value={form.hospital_id}
                      onChange={(event) => setForm({ ...form, hospital_id: event.target.value })}
                      required
                    >
                      <option value="">Select hospital</option>
                      {hospitals.map((hospital) => (
                        <option key={hospital.hospital_id} value={hospital.hospital_id}>
                          {hospital.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Recipient</label>
                    <select
                      className="form-select"
                      value={form.recipient_id}
                      onChange={(event) => setForm({ ...form, recipient_id: event.target.value })}
                      required
                    >
                      <option value="">Select recipient</option>
                      {recipients.map((recipient) => (
                        <option key={recipient.recipient_id} value={recipient.recipient_id}>
                          {recipient.name} ({recipient.blood_group})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Blood component</label>
                      <select
                        className="form-select"
                        value={form.component_type}
                        onChange={(event) => setForm({ ...form, component_type: event.target.value })}
                      >
                        {COMPONENTS.map((component) => (
                          <option key={component} value={component}>{readable(component)}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Quantity</label>
                      <input
                        className="form-input"
                        type="number"
                        min="1"
                        value={form.quantity}
                        onChange={(event) => setForm({ ...form, quantity: event.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Urgency</label>
                    <select
                      className="form-select"
                      value={form.urgency}
                      onChange={(event) => setForm({ ...form, urgency: event.target.value })}
                    >
                      {URGENCIES.map((urgency) => (
                        <option key={urgency} value={urgency}>{readable(urgency)}</option>
                      ))}
                    </select>
                  </div>

                  {hospitals.length === 0 && (
                    <div className="inline-alert error-alert">
                      Add a hospital before creating a request.
                    </div>
                  )}
                  {recipients.length === 0 && (
                    <div className="inline-alert error-alert">
                      Register a recipient before creating a request.
                    </div>
                  )}
                </>
              )}

              {error && <div className="form-error">{error}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowForm(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={saving || (type === 'requests' && (!hospitals.length || !recipients.length))}
                >
                  {saving ? 'Saving...' : editing ? 'Save changes' : 'Create record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
