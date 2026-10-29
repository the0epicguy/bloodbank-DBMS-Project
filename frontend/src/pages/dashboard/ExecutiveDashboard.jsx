import React, { useEffect, useState } from 'react';
import api from '../../api/client';

/**
 * ExecutiveDashboard (Person 4) — headline numbers, stock vs critical reserve,
 * units about to expire, and fulfilment by urgency. Data comes from /reports/*.
 */
const STATUS_CLASS = { CRITICAL: 'stock-critical', LOW: 'stock-low', HEALTHY: 'stock-healthy' };

export default function ExecutiveDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      api.getSummary(),
      api.getStockDistribution(),
      api.getExpiringSoon(),
      api.getFulfillmentMetrics(),
    ])
      .then(([summary, stock, expiring, metrics]) =>
        setData({ summary, stock, expiring, metrics })
      )
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="form-error">Failed to load dashboard: {error}</div>;
  if (!data)
    return (
      <div className="empty-state loading">
        <div className="empty-state-icon">⏳</div>
        <div className="empty-state-text">Loading dashboard…</div>
      </div>
    );

  const { summary, stock, expiring, metrics } = data;
  const maxStock = Math.max(stock.critical_threshold * 3, ...stock.groups.map((g) => g.total));
  const soon = [...expiring.within_7_days, ...expiring.within_14_days];

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Executive Dashboard</h1>
          <p className="page-subtitle">Live overview of stock, demand and fulfilment</p>
        </div>
      </div>

      {/* Alerts */}
      {(summary.emergency_open > 0 ||
        stock.critical_groups.length > 0 ||
        expiring.expired_not_swept > 0) && (
        <div className="alert-stack">
          {summary.emergency_open > 0 && (
            <div className="alert alert-danger">
              🚨 {summary.emergency_open} EMERGENCY request(s) waiting for blood
            </div>
          )}
          {stock.critical_groups.length > 0 && (
            <div className="alert alert-warning">
              ⚠️ Critical stock (below {stock.critical_threshold} units):{' '}
              <strong>{stock.critical_groups.join(', ')}</strong>
            </div>
          )}
          {expiring.expired_not_swept > 0 && (
            <div className="alert alert-warning">
              🧪 {expiring.expired_not_swept} past-expiry unit(s) still marked AVAILABLE — run the
              expiry sweep
            </div>
          )}
        </div>
      )}

      {/* Metric cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon green">🩸</div>
          <div>
            <div className="stat-value">{summary.available_units}</div>
            <div className="stat-label">Usable Units</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏳</div>
          <div>
            <div className="stat-value">{summary.expiring_7_days}</div>
            <div className="stat-label">Expiring ≤ 7 days</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">🏥</div>
          <div>
            <div className="stat-value">{summary.open_requests}</div>
            <div className="stat-label">Open Requests</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">📦</div>
          <div>
            <div className="stat-value">{summary.issued_this_month}</div>
            <div className="stat-label">Issued This Month</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">👥</div>
          <div>
            <div className="stat-value">{summary.total_donors}</div>
            <div className="stat-label">Donors</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div>
            <div className="stat-value">{metrics.overall_fulfillment_rate_pct}%</div>
            <div className="stat-label">Overall Fulfilment</div>
          </div>
        </div>
      </div>

      <div className="dash-grid">
        {/* Stock distribution */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Stock by Blood Group</h2>
            <small>Critical reserve: {stock.critical_threshold} units</small>
          </div>
          <div className="bar-chart">
            {stock.groups.map((g) => (
              <div className="bar-row" key={g.blood_group}>
                <span className="blood-group">{g.blood_group}</span>
                <div className="bar-track">
                  <div
                    className={`bar-fill ${STATUS_CLASS[g.status]}`}
                    style={{ width: `${(g.total / maxStock) * 100}%` }}
                  />
                  <div
                    className="bar-threshold"
                    style={{ left: `${(stock.critical_threshold / maxStock) * 100}%` }}
                  />
                </div>
                <span className="bar-value">{g.total}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Expiring soon */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Expiring Soon</h2>
            <small>
              {expiring.count_7_days} within 7 days · {expiring.count_14_days} in 8–14 days
            </small>
          </div>
          {soon.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🎉</div>
              <div className="empty-state-text">Nothing expiring in the next 14 days</div>
            </div>
          ) : (
            <div className="table-container" style={{ maxHeight: 300, overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Unit</th>
                    <th>Group</th>
                    <th>Component</th>
                    <th>Expires</th>
                  </tr>
                </thead>
                <tbody>
                  {soon.map((u) => (
                    <tr key={`${u.bank_id}-${u.unit_id}`}>
                      <td>
                        B{u.bank_id}-U{u.unit_id}
                      </td>
                      <td>
                        <span className="blood-group">{u.blood_group}</span>
                      </td>
                      <td>{u.component_type.replace('_', ' ')}</td>
                      <td>
                        <span className={`badge ${u.days_to_expiry <= 7 ? 'badge-red' : 'badge-yellow'}`}>
                          {u.days_to_expiry}d
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Fulfilment by urgency */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h2 className="card-title">Fulfilment by Urgency</h2>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Urgency</th>
                <th>Requests</th>
                <th>Fulfilled</th>
                <th>Partial</th>
                <th>Pending</th>
                <th>Units (issued / requested)</th>
                <th>Rate</th>
                <th>Avg turnaround</th>
              </tr>
            </thead>
            <tbody>
              {metrics.by_urgency.map((m) => (
                <tr key={m.urgency}>
                  <td>
                    <span className={`badge urgency-${m.urgency}`}>{m.urgency}</span>
                  </td>
                  <td>{m.total_requests}</td>
                  <td>{m.fulfilled}</td>
                  <td>{m.partially_fulfilled}</td>
                  <td>{m.pending}</td>
                  <td>
                    {m.units_issued} / {m.units_requested}
                  </td>
                  <td>
                    <div className="mini-progress">
                      <div className="mini-progress-fill" style={{ width: `${m.fulfillment_rate_pct}%` }} />
                    </div>
                    <small>{m.fulfillment_rate_pct}%</small>
                  </td>
                  <td>{m.avg_turnaround_days == null ? '—' : `${m.avg_turnaround_days} d`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
