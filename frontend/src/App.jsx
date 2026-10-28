import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import DonorList from './pages/donors/DonorList';
import DonorDetail from './pages/donors/DonorDetail';

/**
 * Main App component.
 * Renders the sidebar navigation and routes.
 */
export default function App() {
  return (
    <BrowserRouter>
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
            <div className="nav-section-title">Person 1 — Donors</div>
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `nav-link ${isActive ? 'active' : ''}`
              }
            >
              <span className="nav-link-icon">👥</span>
              Donor List
            </NavLink>

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
            <span className="nav-link" style={{ opacity: 0.4, cursor: 'default' }}>
              <span className="nav-link-icon">📊</span>
              Reports (P4)
            </span>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DonorList />} />
            <Route path="/donors/:id" element={<DonorDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
