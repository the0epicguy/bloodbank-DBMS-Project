import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';

import ExecutiveDashboard from './pages/dashboard/ExecutiveDashboard';
import DonorList from './pages/donors/DonorList';
import DonorDetail from './pages/donors/DonorDetail';
import BankList from './pages/inventory/BankList';
import InventoryDashboard from './pages/inventory/InventoryDashboard';
import ExpirySweepAction from './pages/inventory/ExpirySweepAction';
import P3Manager from './pages/P3Manager';
import IssueLog from './pages/issues/IssueLog';

const navClass = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`;

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        {/* ── Sidebar ─────────────────────────────────────────────── */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <NavLink to="/banks" className="sidebar-logo">
              <div className="sidebar-logo-icon">🩸</div>
              <div>
                <div className="sidebar-logo-text">BloodBank</div>
                <div className="sidebar-logo-sub">Management System</div>
              </div>
            </NavLink>
          </div>

          <nav className="sidebar-nav">
            {/* Direct Bank & Inventory Section (Person 2) */}
            <div className="nav-section-title">Blood Banks & Inventory (P2)</div>
            <NavLink to="/banks" className={navClass}>
              <span className="nav-link-icon">🏥</span>Blood Banks
            </NavLink>
            <NavLink to="/inventory" className={navClass}>
              <span className="nav-link-icon">🧬</span>Stock Matrix
            </NavLink>
            <NavLink to="/sweep" className={navClass}>
              <span className="nav-link-icon">🧹</span>Expiry Sweep
            </NavLink>

            {/* Overview / Analytics */}
            <div className="nav-section-title" style={{ marginTop: '1.25rem' }}>
              Overview
            </div>
            <NavLink to="/dashboard" className={navClass}>
              <span className="nav-link-icon">📊</span>Dashboard
            </NavLink>

            {/* Donors (Person 1) */}
            <div className="nav-section-title" style={{ marginTop: '1.25rem' }}>
              Donors & Donations (P1)
            </div>
            <NavLink to="/donors" className={navClass}>
              <span className="nav-link-icon">👤</span>Donor List
            </NavLink>

            {/* Requests & Master Records (Person 3) */}
            <div className="nav-section-title" style={{ marginTop: '1.25rem' }}>
              Hospitals & Requests (P3)
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

            {/* Fulfilment & Issues (Person 4) */}
            <div className="nav-section-title" style={{ marginTop: '1.25rem' }}>
              Fulfilment & Audit (P4)
            </div>
            <NavLink to="/issues" className={navClass}>
              <span className="nav-link-icon">💉</span>Issue Log
            </NavLink>
          </nav>

          <div className="sidebar-user">
            <div className="sidebar-user-name">DBMS Portal</div>
            <div className="sidebar-user-role" style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.65rem' }}>●</span> Open Access Mode
            </div>
          </div>
        </aside>

        {/* ── Main Content Area ───────────────────────────────────── */}
        <main className="main-content">
          <Routes>
            {/* Direct Bank Page as default landing page */}
            <Route path="/" element={<Navigate to="/banks" replace />} />

            {/* P2 – Blood Banks & Cold Storage Inventory */}
            <Route path="/banks" element={<BankList />} />
            <Route path="/inventory" element={<InventoryDashboard />} />
            <Route path="/sweep" element={<ExpirySweepAction />} />

            {/* Overview Dashboard */}
            <Route path="/dashboard" element={<ExecutiveDashboard />} />

            {/* P1 – Donors & Donations */}
            <Route path="/donors" element={<DonorList />} />
            <Route path="/donors/:id" element={<DonorDetail />} />

            {/* P3 – Hospitals, Recipients, Blood Requests */}
            <Route path="/hospitals" element={<P3Manager type="hospitals" />} />
            <Route path="/recipients" element={<P3Manager type="recipients" />} />
            <Route path="/requests" element={<P3Manager type="requests" />} />

            {/* P4 – Issues & Allocation */}
            <Route path="/issues" element={<IssueLog />} />

            {/* Catch-all redirect to /banks */}
            <Route path="*" element={<Navigate to="/banks" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
