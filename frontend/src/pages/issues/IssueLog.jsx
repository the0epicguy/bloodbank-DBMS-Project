import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/client';
import FulfillRequestModal from './FulfillRequestModal';

/**
 * IssueLog page (Person 4)
 *  - "Open requests" queue (EMERGENCY first) with a Fulfil button (bank staff / admin)
 *  - Audit log of every unit ever issued, with filters and paging
 */
const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const PAGE_SIZE = 15;

export default function IssueLog() {
  const [pending, setPending] = useState([]);
  const [issues, setIssues] = useState({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ blood_group: '', date_from: '', date_to: '' });
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, i] = await Promise.all([
        api.getPendingRequests(),
        api.getIssues({ ...filters, skip: page * PAGE_SIZE, limit: PAGE_SIZE }),
      ]);
      setPending(p);
      setIssues(i);
    } catch (err) {
      showToast('Failed to load: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    load();
  }, [load]);

  const setFilter = (key, value) => {
    setFilters({ ...filters, [key]: value });
    setPage(0);
  };

  const pages = Math.max(1, Math.ceil(issues.total / PAGE_SIZE));

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Issue Log</h1>
          <p className="page-subtitle">
            Blood fulfilment & audit trail · {issues.total} units issued · {pending.length} open
            requests
          </p>
        </div>
      </div>

      {/* Open requests */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h2 className="card-title">Open Requests</h2>
        </div>
        {pending.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">✅</div>
            <div className="empty-state-text">No open requests</div>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Urgency</th>
                  <th>Hospital</th>
                  <th>Patient</th>
                  <th>Needs</th>
                  <th>Progress</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {pending.map((r) => (
                  <tr key={r.request_id}>
                    <td>{r.request_id}</td>
                    <td>
                      <span className={`badge urgency-${r.urgency}`}>{r.urgency}</span>
                    </td>
                    <td>{r.hospital_name}</td>
                    <td>{r.recipient_name}</td>
                    <td>
                      <span className="blood-group">{r.blood_group}</span>{' '}
                      {r.component_type.replace('_', ' ')}
                    </td>
                    <td>
                      <div className="mini-progress" title={`${r.issued_units}/${r.quantity}`}>
                        <div
                          className="mini-progress-fill"
                          style={{ width: `${(r.issued_units / r.quantity) * 100}%` }}
                        />
                      </div>
                      <small>
                        {r.issued_units}/{r.quantity}
                      </small>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          r.status === 'PARTIALLY_FULFILLED' ? 'badge-yellow' : 'badge-blue'
                        }`}
                      >
                        {r.status.replace('_', ' ')}
                      </span>
                    </td>
                      <td>
                        <button className="btn btn-primary btn-sm" onClick={() => setSelected(r)}>
                          Fulfil
                        </button>
                      </td>
                    </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit log */}
      <div className="filters-bar">
        <select
          className="form-select"
          value={filters.blood_group}
          onChange={(e) => setFilter('blood_group', e.target.value)}
        >
          <option value="">All Blood Groups</option>
          {BLOOD_GROUPS.map((g) => (
            <option key={g}>{g}</option>
          ))}
        </select>
        <input
          type="date"
          className="form-input"
          value={filters.date_from}
          onChange={(e) => setFilter('date_from', e.target.value)}
          title="From date"
        />
        <input
          type="date"
          className="form-input"
          value={filters.date_to}
          onChange={(e) => setFilter('date_to', e.target.value)}
          title="To date"
        />
      </div>

      {loading ? (
        <div className="empty-state loading">
          <div className="empty-state-icon">⏳</div>
          <div className="empty-state-text">Loading…</div>
        </div>
      ) : issues.items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-text">No issued units yet</div>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Issue</th>
                <th>Date</th>
                <th>Unit</th>
                <th>Group</th>
                <th>Donor</th>
                <th>Bank</th>
                <th>Patient</th>
                <th>Hospital</th>
                <th>Urgency</th>
                <th>By</th>
              </tr>
            </thead>
            <tbody>
              {issues.items.map((i) => (
                <tr key={i.issue_id}>
                  <td>#{i.issue_id}</td>
                  <td>{new Date(i.issue_date).toLocaleString()}</td>
                  <td>
                    B{i.bank_id}-U{i.unit_id}
                    <div>
                      <small>{i.component_type.replace('_', ' ')}</small>
                    </div>
                  </td>
                  <td>
                    <span className="blood-group">{i.blood_group}</span>
                  </td>
                  <td>{i.donor_name}</td>
                  <td>{i.bank_name}</td>
                  <td>
                    {i.recipient_name}{' '}
                    <span className="blood-group">{i.recipient_blood_group}</span>
                  </td>
                  <td>{i.hospital_name}</td>
                  <td>
                    <span className={`badge urgency-${i.urgency}`}>{i.urgency}</span>
                  </td>
                  <td>{i.issued_by_name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pages > 1 && (
        <div className="pager">
          <button className="btn btn-secondary btn-sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
            ← Prev
          </button>
          <span>
            Page {page + 1} of {pages}
          </span>
          <button
            className="btn btn-secondary btn-sm"
            disabled={page + 1 >= pages}
            onClick={() => setPage(page + 1)}
          >
            Next →
          </button>
        </div>
      )}

      {selected && (
        <FulfillRequestModal
          request={selected}
          onClose={() => setSelected(null)}
          onDone={(msg) => {
            setSelected(null);
            showToast(msg);
            load();
          }}
        />
      )}

      {toast && <div className={`toast toast-${toast.type}`}>{toast.message}</div>}
    </>
  );
}
