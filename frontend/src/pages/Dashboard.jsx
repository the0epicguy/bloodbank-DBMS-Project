
import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import api from '../api/client';

const initialStats = {
  donors: 0,
  hospitals: 0,
  recipients: 0,
  requests: 0,
  pending: 0,
};

function StatCard({ title, value, description, icon, color }) {
  return (
    <div className="dashboard-stat-card">
      <div className="dashboard-stat-top">
        <span className="dashboard-stat-label">{title}</span>
        <span
          className="dashboard-stat-icon"
          style={{ color, background: `${color}12` }}
        >
          {icon}
        </span>
      </div>
      <div className="dashboard-stat-value">{value}</div>
      <div className="dashboard-stat-description">{description}</div>
    </div>
  );
}

function statusClass(status) {
  return `status-pill status-${String(status || 'pending')
    .toLowerCase()
    .replaceAll('_', '-')}`;
}

export default function Dashboard() {
  const [stats, setStats] = useState(initialStats);
  const [recentRequests, setRecentRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setLoading(true);
      setError('');

      const results = await Promise.allSettled([
        api.getDonors(),
        api.getHospitals(),
        api.getRecipients(),
        api.getRequests(),
      ]);

      if (!active) return;

      const [donors, hospitals, recipients, requests] = results;

      const count = (result) =>
        result.status === 'fulfilled' && Array.isArray(result.value)
          ? result.value.length
          : 0;

      const requestList =
        requests.status === 'fulfilled' && Array.isArray(requests.value)
          ? requests.value
          : [];

      setStats({
        donors: count(donors),
        hospitals: count(hospitals),
        recipients: count(recipients),
        requests: requestList.length,
        pending: requestList.filter(
          (item) =>
            item.status === 'PENDING' ||
            item.status === 'PARTIALLY_FULFILLED'
        ).length,
      });

      setRecentRequests(
        [...requestList]
          .sort(
            (a, b) =>
              new Date(b.request_date).getTime() -
              new Date(a.request_date).getTime()
          )
          .slice(0, 5)
      );

      if (results.every((result) => result.status === 'rejected')) {
        setError('Could not load dashboard data. Check that the backend is running.');
      }

      setLoading(false);
    }

    loadDashboard();

    return () => {
      active = false;
    };
  }, []);

  const formatDate = (date) => {
    if (!date) return '—';

    const parsed = new Date(date);
    return Number.isNaN(parsed.getTime())
      ? '—'
      : parsed.toLocaleDateString('en-IN', {
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        });
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-welcome">
        <div>
          <div className="dashboard-eyebrow">OVERVIEW</div>
          <h1>Dashboard</h1>
          <p>Welcome back. Here's your blood bank at a glance.</p>
        </div>

        <NavLink to="/requests" className="btn btn-primary">
          + New Blood Request
        </NavLink>
      </div>

      {error && <div className="dashboard-error">{error}</div>}

      <div className="dashboard-section-heading">
        <div>
          <h2>Key statistics</h2>
          <p>A snapshot of your registered records</p>
        </div>
      </div>

      <div className="dashboard-stats-grid">
        <StatCard
          title="Total Donors"
          value={loading ? '...' : stats.donors}
          description="Registered blood donors"
          icon="D"
          color="#c6283d"
        />
        <StatCard
          title="Hospitals"
          value={loading ? '...' : stats.hospitals}
          description="Registered hospitals"
          icon="H"
          color="#3267c8"
        />
        <StatCard
          title="Recipients"
          value={loading ? '...' : stats.recipients}
          description="People registered"
          icon="R"
          color="#8b5ac8"
        />
        <StatCard
          title="Pending Requests"
          value={loading ? '...' : stats.pending}
          description={`${stats.requests} total blood requests`}
          icon="!"
          color="#d97706"
        />
      </div>

      <div className="dashboard-content-grid">
        <section className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h2>Recent blood requests</h2>
              <p>Latest requests recorded in the system</p>
            </div>
            <NavLink to="/requests" className="dashboard-text-link">
              View all
            </NavLink>
          </div>

          {loading ? (
            <div className="dashboard-empty">Loading requests...</div>
          ) : recentRequests.length === 0 ? (
            <div className="dashboard-empty">
              <div className="dashboard-empty-icon">+</div>
              <h3>No requests yet</h3>
              <p>Blood requests will appear here when they are created.</p>
              <NavLink to="/requests" className="dashboard-text-link">
                Create a request
              </NavLink>
            </div>
          ) : (
            <div className="dashboard-table-wrap">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Request</th>
                    <th>Component</th>
                    <th>Urgency</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRequests.map((request) => (
                    <tr key={request.request_id}>
                      <td>#{request.request_id}</td>
                      <td>{String(request.component_type || '').replaceAll('_', ' ')}</td>
                      <td>
                        <span className={statusClass(request.urgency)}>
                          {request.urgency || 'ROUTINE'}
                        </span>
                      </td>
                      <td>
                        <span className={statusClass(request.status)}>
                          {String(request.status || '').replaceAll('_', ' ')}
                        </span>
                      </td>
                      <td>{formatDate(request.request_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="dashboard-panel dashboard-quick-actions">
          <div className="dashboard-panel-header">
            <div>
              <h2>Quick actions</h2>
              <p>Jump straight into a module</p>
            </div>
          </div>

          <NavLink to="/" className="quick-action">
            <span className="quick-action-icon red">D</span>
            <span>
              <strong>Manage donors</strong>
              <small>View, add and update donor records</small>
            </span>
            <span className="quick-action-arrow">›</span>
          </NavLink>

          <NavLink to="/hospitals" className="quick-action">
            <span className="quick-action-icon blue">H</span>
            <span>
              <strong>Manage hospitals</strong>
              <small>Maintain hospital information</small>
            </span>
            <span className="quick-action-arrow">›</span>
          </NavLink>

          <NavLink to="/recipients" className="quick-action">
            <span className="quick-action-icon purple">R</span>
            <span>
              <strong>Manage recipients</strong>
              <small>View and register recipients</small>
            </span>
            <span className="quick-action-arrow">›</span>
          </NavLink>

          <NavLink to="/requests" className="quick-action">
            <span className="quick-action-icon amber">!</span>
            <span>
              <strong>Blood requests</strong>
              <small>Create and track requests</small>
            </span>
            <span className="quick-action-arrow">›</span>
          </NavLink>
        </section>
      </div>
    </div>
  );
}
