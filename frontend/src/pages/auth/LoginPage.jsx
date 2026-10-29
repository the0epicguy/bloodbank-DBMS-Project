import React, { useState } from 'react';
import { useAuth } from '../../auth/AuthContext';

/**
 * LoginPage (Person 4)
 *  - normal username/password login (JWT)
 *  - 4 "1-Click Quick Login" buttons for demos
 */
const QUICK_ROLES = [
  { role: 'ADMIN', icon: '🛡️', label: 'Admin', hint: 'Full access' },
  { role: 'BANK_STAFF', icon: '🏦', label: 'Bank Staff', hint: 'Inventory & issuing' },
  { role: 'HOSPITAL_STAFF', icon: '🏥', label: 'Hospital Staff', hint: 'Requests & issue log' },
  { role: 'DONOR', icon: '🩸', label: 'Donor', hint: 'Donor view' },
];

export default function LoginPage() {
  const { login, demoLogin } = useAuth();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const run = async (fn) => {
    setError('');
    setBusy(true);
    try {
      await fn();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">🩸</div>
        <h1 className="login-title">BloodBank</h1>
        <p className="login-sub">Management System · Sign in</p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            run(() => login(form.username, form.password));
          }}
        >
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              className="form-input"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              autoFocus
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary login-submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="login-divider">
          <span>or 1-click quick login</span>
        </div>

        <div className="quick-grid">
          {QUICK_ROLES.map((r) => (
            <button
              key={r.role}
              className="quick-btn"
              disabled={busy}
              onClick={() => run(() => demoLogin(r.role))}
            >
              <span className="quick-icon">{r.icon}</span>
              <span className="quick-label">{r.label}</span>
              <span className="quick-hint">{r.hint}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
