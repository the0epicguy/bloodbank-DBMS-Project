import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';

import { AuthProvider, useAuth, canSeeReports, canSeeIssues } from './auth/AuthContext';
import LoginPage from './pages/auth/LoginPage';
import ExecutiveDashboard from './pages/dashboard/ExecutiveDashboard';
import DonorList from './pages/donors/DonorList';
import DonorDetail from './pages/donors/DonorDetail';
import BankList from './pages/inventory/BankList';
import InventoryDashboard from './pages/inventory/InventoryDashboard';
import ExpirySweepAction from './pages/inventory/ExpirySweepAction';
import P3Manager from './pages/P3Manager';
import IssueLog from './pages/issues/IssueLog';

const navClass = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`;

/** "/" redirects each role to their most relevant landing page. */
function RoleHome() {
  const { user } = useAuth();
  if (canSeeReports(user)) return <Navigate to="/dashboard" replace />;
  if (canSeeIssues(user)) return <Navigate to="/issues" replace />;
  return <Navigate to="/donors" replace />;
}

/** Renders an "access denied" message when the user's role is not allowed. */
function Guard({ allowed, children }) {
  const { user } = useAuth();
  if (!allowed(user)) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🔒</div>
        <div className="empty-state-text">
          Your role ({user.role.replace(/_/g, ' ')}) cannot open this page.
        </div>
      </div>
    );
  }
  return children;
}

/** The main shell: sidebar + route outlet. Shown after login. */
function Shell() {
  const { user, logout } = useAuth();
  const isAdmin = canSeeReports(user);
  const isStaff = canSeeIssues(user);

  return (
    <div className="app-layout">
      {/* ── Sidebar ─────────────────────────────────────────────── */}
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
          {/* Overview – admin / bank staff only */}
          {isAdmin && (
            <>
              <div className="nav-section-title">Overview</div>
              <NavLink to="/dashboard" className={navClass}>
                <span className="nav-link-icon">📊</span>Dashboard
              </NavLink>
            </>
          )}

          {/* Donors – everyone */}
          <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
            Donors (P1)
          </div>
          <NavLink to="/donors" className={navClass}>
            <span className="nav-link-icon">👤</span>Donor List
          </NavLink>

          {/* Inventory – admin / bank staff only */}
          {isAdmin && (
            <>
              <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
                Inventory (P2)
              </div>
              <NavLink to="/banks" className={navClass}>
                <span className="nav-link-icon">🏥</span>Blood Banks
              </NavLink>
              <NavLink to="/inventory" className={navClass}>
                <span className="nav-link-icon">🧬</span>Stock Matrix
              </NavLink>
              <NavLink to="/sweep" className={navClass}>
                <span className="nav-link-icon">🧹</span>Expiry Sweep
              </NavLink>
            </>
          )}

          {/* Hospitals / Recipients / Requests – staff + admin */}
          {isStaff && (
            <>
              <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
                Requests (P3)
              </div>
              <NavLink to="/hospitals" className={navClass}>
                <span className="nav-link-icon">🏨</span>Hospitals
              </NavLink>
              <NavLink to="/recipients" className={navClass}>
                <span className="nav-link-icon">🫀</span>Recipients
              </NavLink>
              <NavLink to="/requests" className={navClass}>
                <span className="nav-link-icon">📋</span>Blood Requests
              </NavLink>
            </>
          )}

          {/* Issues – staff + admin */}
          {isStaff && (
            <>
              <div className="nav-section-title" style={{ marginTop: '1.5rem' }}>
                Fulfilment (P4)
              </div>
              <NavLink to="/issues" className={navClass}>
                <span className="nav-link-icon">💉</span>Issue Log
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-user-name">{user.full_name}</div>
          <div className="sidebar-user-role">{user.role.replace(/_/g, ' ')}</div>
          <button className="btn btn-secondary btn-sm" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────── */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<RoleHome />} />

          {/* P1 – Donors */}
          <Route path="/donors" element={<DonorList />} />
          <Route path="/donors/:id" element={<DonorDetail />} />

          {/* P2 – Inventory */}
          <Route
            path="/banks"
            element={
              <Guard allowed={canSeeReports}>
                <BankList />
              </Guard>
            }
          />
          <Route
            path="/inventory"
            element={
              <Guard allowed={canSeeReports}>
                <InventoryDashboard />
              </Guard>
            }
          />
          <Route
            path="/sweep"
            element={
              <Guard allowed={canSeeReports}>
                <ExpirySweepAction />
              </Guard>
            }
          />

          {/* P3 – Hospitals / Recipients / Requests */}
          <Route
            path="/hospitals"
            element={
              <Guard allowed={canSeeIssues}>
                <P3Manager type="hospitals" />
              </Guard>
            }
          />
          <Route
            path="/recipients"
            element={
              <Guard allowed={canSeeIssues}>
                <P3Manager type="recipients" />
              </Guard>
            }
          />
          <Route
            path="/requests"
            element={
              <Guard allowed={canSeeIssues}>
                <P3Manager type="requests" />
              </Guard>
            }
          />

          {/* P4 – Issues & Dashboard */}
          <Route
            path="/issues"
            element={
              <Guard allowed={canSeeIssues}>
                <IssueLog />
              </Guard>
            }
          />
          <Route
            path="/dashboard"
            element={
              <Guard allowed={canSeeReports}>
                <ExecutiveDashboard />
              </Guard>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

/** Shows LoginPage until the user is authenticated. */
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
