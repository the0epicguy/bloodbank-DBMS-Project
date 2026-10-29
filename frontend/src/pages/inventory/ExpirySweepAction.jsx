/**
 * ExpirySweepAction.jsx  (Person 2 — converted from ExpirySweepAction.tsx)
 * Admin tool to expire all past-expiry blood units in one click.
 * Rewritten as plain JSX using useState (no react-query/TypeScript).
 */
import React, { useState } from 'react';
import api from '../../api/client';

export default function ExpirySweepAction() {
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  const runSweep = async () => {
    setRunning(true);
    setResult(null);
    setError('');
    try {
      const data = await api.runExpirySweep();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Sweep failed. Check server logs.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Expiry Sweep</h1>
          <p className="page-subtitle">Mark all past-expiry AVAILABLE units as EXPIRED</p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: '560px' }}>
        {/* Info */}
        <div className="card-body">
          <ul className="info-list">
            <li>Scans every <strong>AVAILABLE</strong> blood unit against today's date.</li>
            <li>
              Units with <code>expiry_date &lt; TODAY</code> are set to{' '}
              <span className="badge badge-danger">EXPIRED</span>.
            </li>
            <li>Safe to run multiple times — already-expired units are skipped.</li>
            <li>
              Backed by the MySQL trigger <code>trg_after_issue_insert</code> for atomicity.
            </li>
          </ul>

          <button
            id="btn-run-expiry-sweep"
            className="btn btn-danger"
            style={{ width: '100%', marginTop: '1.5rem', padding: '0.875rem' }}
            onClick={runSweep}
            disabled={running}
          >
            {running ? (
              <>
                <span className="spinner" style={{ marginRight: '0.5rem' }} />
                Running Expiry Sweep…
              </>
            ) : (
              '🧹 Run Expiry Sweep Now'
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="alert alert-error" style={{ marginTop: '1rem' }}>
              ❌ {error}
            </div>
          )}

          {/* Result */}
          {result && !running && (
            <div className="alert alert-success" style={{ marginTop: '1rem' }}>
              <p className="font-medium">✅ Sweep complete</p>
              {result.swept_count === 0 ? (
                <p>All AVAILABLE units are within their expiry date. Nothing to do.</p>
              ) : (
                <>
                  <p>
                    <strong>{result.swept_count}</strong> unit
                    {result.swept_count !== 1 ? 's' : ''} transitioned to{' '}
                    <strong>EXPIRED</strong>.
                  </p>
                  {result.expired_unit_ids?.length > 0 && (
                    <div className="unit-id-list">
                      {result.expired_unit_ids.map(({ bank_id, unit_id }) => (
                        <span
                          key={`${bank_id}-${unit_id}`}
                          className="unit-id-chip"
                        >
                          Bank #{bank_id} · Unit #{unit_id}
                        </span>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
