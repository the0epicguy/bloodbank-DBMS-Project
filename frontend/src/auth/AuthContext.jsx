import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import api, { getToken, setToken, clearToken } from '../api/client';

/**
 * AuthContext (Person 4) — keeps track of who is logged in.
 *
 *   const { user, login, demoLogin, logout } = useAuth();
 *
 * On page load, if a token is saved we ask GET /auth/me to restore the session.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  // Restore session on first load
  useEffect(() => {
    if (!getToken()) return;
    api
      .getMe()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  // api/client.js fires this when the server says the token is no longer valid
  useEffect(() => {
    window.addEventListener('auth:logout', logout);
    return () => window.removeEventListener('auth:logout', logout);
  }, [logout]);

  const finishLogin = (data) => {
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const login = async (username, password) => finishLogin(await api.login(username, password));
  const demoLogin = async (role) => finishLogin(await api.demoLogin(role));

  return (
    <AuthContext.Provider value={{ user, loading, login, demoLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

// Which roles may see which pages (matches the backend rules)
export const canSeeReports = (user) => ['ADMIN', 'BANK_STAFF'].includes(user?.role);
export const canSeeIssues = (user) =>
  ['ADMIN', 'BANK_STAFF', 'HOSPITAL_STAFF'].includes(user?.role);
export const canFulfil = (user) => ['ADMIN', 'BANK_STAFF'].includes(user?.role);
