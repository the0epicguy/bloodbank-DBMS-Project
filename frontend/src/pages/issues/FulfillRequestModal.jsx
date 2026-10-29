import React, { useEffect, useState } from 'react';
import api from '../../api/client';

/**
 * FulfillRequestModal (Person 4)
 * Shows the FEFO (First-Expired-First-Out) recommendation for one request and
 * lets staff either:
 *   - "Auto-fulfil"  -> issue all recommended units in one click, or
 *   - "Issue" on a single recommended unit.
 *
 * Props: request (a row from /issues/pending-requests), onClose(), onDone(message)
 */
export default function FulfillRequestModal({ request, onClose, onDone }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const loadPreview = async () => {
    setLoading(true);
    try {
      setPreview(await api.getFefoPreview(request.request_id));
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPreview();
  }, [request.request_id]);

  const handleAuto = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await api.autoFulfil(request.request_id);
      onDone(res.message);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  const handleManual = async (u) => {
    setBusy(true);
    setError('');
    try {
      const res = await api.manualIssue({
        request_id: request.request_id,
        bank_id: u.bank_id,
        unit_id: u.unit_id,
      });
      if (res.remaining === 0) {
        onDone(res.message);
      } else {
        await loadPreview();
        setBusy(false);
      }
    } catch (err) {
      setError(err.message);
      setBusy(false);
      loadPreview();
    }
  };

  const expiryBadge = (days) =>
    days <= 3 ? 'badge-red' : days <= 7 ? 'badge-yellow' : 'badge-green';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-title">Fulfil Request #{request.request_id}</h2>

        <div className="fulfil-summary">
          <div>
            <div className="stat-label">Patient</div>
            <div>{request.recipient_name}</div>
          </div>
          <div>
            <div className="stat-label">Hospital</div>
            <div>{request.hospital_name}</div>
          </div>
          <div>
            <div className="stat-label">Needs</div>
            <div>
              <span className="blood-group">{request.blood_group}</span>{' '}
              {request.component_type.replace('_', ' ')} × {request.remaining} remaining
            </div>
          </div>
          <div>
            <div className="stat-label">Urgency</div>
            <span className={`badge urgency-${request.urgency}`}>{request.urgency}</span>
          </div>
        </div>

        {loading ? (
          <div className="empty-state loading">
            <div className="empty-state-text">Finding best units…</div>
          </div>
        ) : preview ? (
          <>
            <p className="page-subtitle" style={{ margin: '1rem 0 0.5rem' }}>
              Compatible donor groups: <strong>{preview.compatible_groups.join(', ')}</strong>.
              Units that expire soonest are recommended first (FEFO).
            </p>

            {preview.recommended.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📭</div>
                <div className="empty-state-text">No compatible units in stock right now</div>
              </div>
            ) : (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Unit</th>
                      <th>Group</th>
                      <th>Bank</th>
                      <th>Expires</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.recommended.map((u, i) => (
                      <tr key={`${u.bank_id}-${u.unit_id}`}>
                        <td>{i + 1}</td>
                        <td>
                          B{u.bank_id}-U{u.unit_id}
                        </td>
                        <td>
                          <span className="blood-group">{u.blood_group}</span>
                          {u.exact_group_match && (
                            <span className="badge badge-blue" style={{ marginLeft: 6 }}>
                              exact
                            </span>
                          )}
                        </td>
                        <td>{u.bank_name}</td>
                        <td>
                          <span className={`badge ${expiryBadge(u.days_to_expiry)}`}>
                            {u.expiry_date} · {u.days_to_expiry}d
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-secondary btn-sm"
                            disabled={busy}
                            onClick={() => handleManual(u)}
                          >
                            Issue
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {preview.shortfall > 0 && preview.recommended.length > 0 && (
              <div className="form-error" style={{ marginTop: '0.75rem' }}>
                Stock covers only {preview.recommended.length} of {preview.remaining} units. The
                request will become PARTIALLY_FULFILLED.
              </div>
            )}
          </>
        ) : null}

        {error && <div className="form-error">{error}</div>}

        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button
            className="btn btn-primary"
            disabled={busy || loading || !preview || preview.recommended.length === 0}
            onClick={handleAuto}
          >
            {busy ? 'Allocating…' : `⚡ Auto-fulfil (${preview?.recommended.length ?? 0} units)`}
          </button>
        </div>
      </div>
    </div>
  );
}
