/**
 * InventoryDashboard.jsx  (Person 2 — converted from InventoryDashboard.tsx)
 * Blood-group × component stock matrix across all banks.
 * Rewritten as plain JSX using useState/useEffect (no react-query/TypeScript).
 */
import React, { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';

const BLOOD_GROUPS = ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'];
const COMPONENTS = ['WHOLE_BLOOD', 'RBC', 'PLATELETS', 'PLASMA'];
const COMPONENT_LABELS = {
  WHOLE_BLOOD: 'Whole Blood',
  RBC: 'RBC',
  PLATELETS: 'Platelets',
  PLASMA: 'Plasma',
};

function expiryColor(daysLeft) {
  if (daysLeft === undefined || daysLeft === null) return 'cell-ok';
  if (daysLeft <= 3) return 'cell-critical';
  if (daysLeft <= 7) return 'cell-warning';
  if (daysLeft <= 14) return 'cell-caution';
  return 'cell-ok';
}

function MatrixCell({ units, earliestExpiry }) {
  const daysLeft = earliestExpiry
    ? Math.ceil((new Date(earliestExpiry).getTime() - Date.now()) / 86_400_000)
    : undefined;
  const cls = units === 0 ? 'cell-empty' : expiryColor(daysLeft);

  return (
    <td>
      <div
        className={`matrix-cell ${cls}`}
        title={
          earliestExpiry
            ? `Earliest expiry: ${earliestExpiry} (${daysLeft}d)`
            : 'No available units'
        }
      >
        <span className="matrix-cell-count">{units}</span>
        {daysLeft !== undefined && units > 0 && (
          <span className="matrix-cell-days">{daysLeft}d left</span>
        )}
      </div>
    </td>
  );
}

export default function InventoryDashboard() {
  const [banks, setBanks] = useState([]);
  const [selectedBankId, setSelectedBankId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [globalSummary, setGlobalSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState('');

  // Load bank list once
  useEffect(() => {
    api.getBanks()
      .then((data) => setBanks(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Load stock summary whenever selectedBankId changes
  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    setError('');
    try {
      // /inventory/summary returns { banks, total_available, low_stock_alerts }
      const resp = await api.getInventorySummary(selectedBankId);
      // Flatten all bank matrix rows into one array for the grid
      let rows = [];
      if (resp && Array.isArray(resp.banks)) {
        resp.banks.forEach((b) => { if (Array.isArray(b.matrix)) rows = rows.concat(b.matrix); });
      }
      setSummary(rows);
      setGlobalSummary(resp || null);
    } catch (err) {
      setError(err.message || 'Failed to load inventory.');
    } finally {
      setSummaryLoading(false);
    }
  }, [selectedBankId]);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  // Build lookup map for matrix: "GROUP::COMPONENT" → cell data
  const matrixMap = new Map(
    (summary || []).map((row) => [`${row.blood_group}::${row.component_type}`, row])
  );

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Inventory Dashboard</h1>
          <p className="page-subtitle">Blood group × component stock matrix</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Global headline numbers */}
      {globalSummary && (
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-value">{globalSummary.total_available?.toLocaleString() ?? 0}</div>
            <div className="stat-label">Total Available Units</div>
          </div>
          <div className="stat-card">
            <div className="stat-value warning">{globalSummary.low_stock_alerts?.length ?? 0}</div>
            <div className="stat-label">Low Stock Alerts</div>
          </div>
          <div className="stat-card">
            <div className="stat-value danger">
              {globalSummary.low_stock_alerts?.filter((a) => a.available_units === 0).length ?? 0}
            </div>
            <div className="stat-label">Critical (0 units)</div>
          </div>
        </div>
      )}

      <div className="inventory-layout">
        {/* Bank selector */}
        <div className="bank-selector">
          <h3 className="section-title">Filter by Bank</h3>
          {loading ? (
            <div className="text-secondary">Loading banks…</div>
          ) : (
            <>
              <button
                className={`bank-card ${selectedBankId === null ? 'selected' : ''}`}
                onClick={() => setSelectedBankId(null)}
              >
                <span className="bank-name">All Banks</span>
              </button>
              {banks.map((bank) => (
                <button
                  key={bank.bank_id}
                  className={`bank-card ${selectedBankId === bank.bank_id ? 'selected' : ''}`}
                  onClick={() =>
                    setSelectedBankId((prev) =>
                      prev === bank.bank_id ? null : bank.bank_id
                    )
                  }
                >
                  <span className="bank-name">{bank.name}</span>
                  <span className="bank-meta">{bank.city}</span>
                  <span className={`bank-units ${(bank.available_units ?? 0) === 0 ? 'danger' : ''}`}>
                    {bank.available_units ?? 0} avail.
                  </span>
                </button>
              ))}
            </>
          )}
        </div>

        {/* Stock matrix */}
        <div className="matrix-wrapper">
          <div className="matrix-legend">
            <span className="legend-item cell-ok">Good</span>
            <span className="legend-item cell-caution">Exp &lt;14d</span>
            <span className="legend-item cell-warning">Exp &lt;7d</span>
            <span className="legend-item cell-critical">Exp &lt;3d</span>
            <span className="legend-item cell-empty">None</span>
          </div>

          {summaryLoading ? (
            <div className="empty-state"><div className="empty-state-text">Loading…</div></div>
          ) : (
            <div className="table-container">
              <table className="table matrix-table">
                <thead>
                  <tr>
                    <th>Group</th>
                    {COMPONENTS.map((c) => (
                      <th key={c} className="text-center">{COMPONENT_LABELS[c]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {BLOOD_GROUPS.map((group) => (
                    <tr key={group}>
                      <td>
                        <span className="blood-group-badge">{group}</span>
                      </td>
                      {COMPONENTS.map((comp) => {
                        const cell = matrixMap.get(`${group}::${comp}`);
                        return (
                          <MatrixCell
                            key={comp}
                            units={cell?.available_units ?? 0}
                            earliestExpiry={cell?.earliest_expiry ?? null}
                          />
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
