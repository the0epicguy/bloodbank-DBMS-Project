import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import DonorList from './pages/donors/DonorList';
import DonorDetail from './pages/donors/DonorDetail';
import LoginPage from './pages/auth/LoginPage';
import IssueLog from './pages/issues/IssueLog';
import ExecutiveDashboard from './pages/dashboard/ExecutiveDashboard';
import { AuthProvider, useAuth, canSeeReports, canSeeIssues } from './auth/AuthContext';

const navClass = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`;

/** "/" sends each role to the page that makes the most sense for them. */
function RoleHome() {
  const { user } = useAuth();
  if (canSeeReports(user)) return <Navigate to="/dashboard" replace />;
  if (canSeeIssues(user)) return <Navigate to="/issues" replace />;
  return <Navigate to="/donors" replace />;
}

/** Only render children if the user's role passes `allowed(user)`. */
function Guard({ allowed, children }) {
  const { user } = useAuth();
  if (!allowed(user)) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🔒</div>
        <div className="empty-state-text">
          Your role ({user.role.replace('_', ' ')}) cannot open this page
        </div>
      </div>
    );
  }
  return children;
}

function Shell() {
  const { user, logout } = useAuth();

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <a href="/" className="sidebar-logo">
            <div className="sidebar-logo-icon">🩸</div>
            <div>
              <div className="sidebar-logo-text">BloodBank</div>
              <div className="sidebar-logo-sub">Management System</div>
            </div>
          </a>
        </div>

        <nav className="sidebar-nav">
          {canSeeReports(user) && (
            <>
              <div className="nav-section-title">Overview</div>
              <NavLink to="/dashboard" className={navClass}>
                <span className="nav-link-icon">📊</span>
                Dashboard
              </NavLink>
            </>
          )}

          <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
            Donors
          </div>
          <NavLink to="/donors" className={navClass}>
            <span className="nav-link-icon">👥</span>
            Donor List
          </NavLink>

          {canSeeIssues(user) && (
            <>
              <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
                Fulfilment
              </div>
              <NavLink to="/issues" className={navClass}>
                <span className="nav-link-icon">📦</span>
                Issue Log
              </NavLink>
            </>
          )}

          <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
            Other Modules
          </div>
          <span className="nav-link" style={{ opacity: 0.4, cursor: 'default' }}>
            <span className="nav-link-icon">🏦</span>
            Inventory (P2)
          </span>
          <span className="nav-link" style={{ opacity: 0.4, cursor: 'default' }}>
            <span className="nav-link-icon">🏥</span>
            Requests (P3)
          </span>
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-user-name">{user.full_name}</div>
          <div className="sidebar-user-role">{user.role.replace('_', ' ')}</div>
          <button className="btn btn-secondary btn-sm" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<RoleHome />} />
          <Route path="/donors" element={<DonorList />} />
          <Route path="/donors/:id" element={<DonorDetail />} />
          <Route
            path="/dashboard"
            element={
              <Guard allowed={canSeeReports}>
                <ExecutiveDashboard />
              </Guard>
            }
          />
          <Route
            path="/issues"
            element={
              <Guard allowed={canSeeIssues}>
                <IssueLog />
              </Guard>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

/** Shows the login page until someone is signed in. */
function Gate() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="empty-state loading">
        <div className="empty-state-text">Loading…</div>
      </div>
    );
  }
  return user ? <Shell /> : <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Gate />
      </BrowserRouter>
    </AuthProvider>
  );
}
