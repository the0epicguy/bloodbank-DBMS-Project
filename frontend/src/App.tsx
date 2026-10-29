import React from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import InventoryDashboard from "./pages/inventory/InventoryDashboard";
import BankList from "./pages/inventory/BankList";
import ExpirySweepAction from "./pages/inventory/ExpirySweepAction";

// ─── Placeholder pages (filled in by other team members) ────────────────────
const Placeholder = ({ title }: { title: string }) => (
  <div className="min-h-screen bg-slate-950 flex items-center justify-center">
    <div className="text-center">
      <div className="text-5xl mb-4">🚧</div>
      <h2 className="text-xl font-bold text-white mb-2">{title}</h2>
      <p className="text-slate-400 text-sm">This page is being implemented by another team member.</p>
    </div>
  </div>
);

// ─── Navigation items ────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { to: "/inventory",    label: "🩸 Inventory",   id: "nav-inventory"  },
  { to: "/banks",        label: "🏥 Banks",        id: "nav-banks"      },
  { to: "/donors",       label: "👤 Donors",       id: "nav-donors"     },
  { to: "/requests",     label: "📋 Requests",     id: "nav-requests"   },
  { to: "/issues",       label: "📦 Issues",       id: "nav-issues"     },
  { to: "/dashboard",   label: "📊 Dashboard",    id: "nav-dashboard"  },
];

// ─── Sidebar ─────────────────────────────────────────────────────────────────
function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col min-h-screen">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-rose-600 flex items-center justify-center text-white font-black text-sm">
            🩸
          </div>
          <div>
            <p className="text-white font-bold text-sm leading-tight">BloodBank</p>
            <p className="text-slate-500 text-[10px]">Management System</p>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map(({ to, label, id }) => (
          <NavLink
            key={to}
            id={id}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ` +
              (isActive
                ? "bg-rose-600/20 text-rose-400 border border-rose-600/30"
                : "text-slate-400 hover:text-white hover:bg-slate-800")
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer: Expiry sweep shortcut */}
      <div className="px-3 py-4 border-t border-slate-800">
        <NavLink
          to="/sweep"
          id="nav-sweep"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ` +
            (isActive
              ? "bg-rose-600/20 text-rose-400 border border-rose-600/30"
              : "text-slate-500 hover:text-white hover:bg-slate-800")
          }
        >
          🗑 Expiry Sweep
        </NavLink>
        <p className="text-slate-600 text-[10px] px-3 mt-3">DBMS Project — Team 2</p>
      </div>
    </aside>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-950">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/"           element={<Navigate to="/inventory" replace />} />
            <Route path="/inventory"  element={<InventoryDashboard />} />
            <Route path="/banks"      element={<BankList />} />
            <Route path="/sweep"      element={
              <div className="p-8">
                <h1 className="text-2xl font-bold text-white mb-6">🗑 Expiry Sweep</h1>
                <ExpirySweepAction />
              </div>
            } />
            {/* Stubs for other persons' pages */}
            <Route path="/donors"    element={<Placeholder title="Donor Management (Person 1)" />} />
            <Route path="/requests"  element={<Placeholder title="Requests & Triage (Person 3)" />} />
            <Route path="/issues"    element={<Placeholder title="Issue Log & Fulfillment (Person 4)" />} />
            <Route path="/dashboard" element={<Placeholder title="Executive Dashboard (Person 4)" />} />
            <Route path="*"          element={<Navigate to="/inventory" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
