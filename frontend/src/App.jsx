
import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import DonorList from './pages/donors/DonorList';
import DonorDetail from './pages/donors/DonorDetail';
import Dashboard from './pages/Dashboard';
import P3Manager from './pages/P3Manager';

const navigation = [
  {
    heading: 'OVERVIEW',
    links: [{ to: '/dashboard', label: 'Dashboard', icon: '▦' }],
  },
  {
    heading: 'PEOPLE',
    links: [
      { to: '/', label: 'Blood donors', icon: '◉', end: true },
      { to: '/hospitals', label: 'Hospitals', icon: '⌂' },
      { to: '/recipients', label: 'Recipients', icon: '♡' },
    ],
  },
  {
    heading: 'OPERATIONS',
    links: [
      { to: '/requests', label: 'Blood requests', icon: '≋' },
    ],
  },
];

function AppLayout() {
  const location = useLocation();

  const pageTitle =
    location.pathname.startsWith('/donors/')
      ? 'Donor profile'
      : [...navigation.flatMap((section) => section.links)]
          .find((link) => link.to === location.pathname)?.label || 'Blood Bank';

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <NavLink to="/dashboard" className="brand">
          <span className="brand-mark">+</span>
          <span>
            <strong>LifeLine</strong>
            <small>Blood Bank Management</small>
          </span>
        </NavLink>

        <div className="sidebar-caption">WORKSPACE</div>

        <nav className="sidebar-nav">
          {navigation.map((section) => (
            <div className="nav-section" key={section.heading}>
              <div className="nav-section-title">{section.heading}</div>
              {section.links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.end}
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-link-icon">{link.icon}</span>
                  {link.label}
                  {link.to === '/requests' && <span className="nav-arrow">›</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="footer-symbol">+</div>
          <div>
            <strong>Every drop counts.</strong>
            <small>One system. Better coordination.</small>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> {pageTitle}</div>
          <div className="system-status">
            <span className="status-dot" />
            Blood bank system
          </div>
        </header>

        <div className="page-content">
          <Routes>
            <Route path="/" element={<DonorList />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/donors/:id" element={<DonorDetail />} />
            <Route path="/hospitals" element={<P3Manager type="hospitals" />} />
            <Route path="/recipients" element={<P3Manager type="recipients" />} />
            <Route path="/requests" element={<P3Manager type="requests" />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
