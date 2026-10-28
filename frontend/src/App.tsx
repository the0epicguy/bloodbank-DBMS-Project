import { useState } from "react";
import { HeartPulse, LayoutDashboard, ClipboardList, ShieldCheck, LogOut, Droplet, AlertTriangle, RefreshCw } from "lucide-react";
import LoginPage from "./pages/auth/LoginPage";
import IssueLog from "./pages/issues/IssueLog";
import Dashboard from "./pages/dashboard/ExecutiveDashboard";
import "./styles.css";

export default function App() {
  const [session, setSession] = useState<any>(() => {
    const token = localStorage.getItem("bb_token");
    const user = localStorage.getItem("bb_user");
    return token && user ? { access_token: token, user: JSON.parse(user) } : null;
  });
  const [page, setPage] = useState("dashboard");
  function signIn(data: any) {
    localStorage.setItem("bb_token", data.access_token);
    localStorage.setItem("bb_user", JSON.stringify(data.user));
    setSession(data);
  }
  function signOut() { localStorage.removeItem("bb_token"); localStorage.removeItem("bb_user"); setSession(null); }
  if (!session) return <LoginPage onLogin={signIn} />;
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-icon"><HeartPulse size={22}/></span><span>Hema<span className="brand-light">Track</span><small>Blood Bank Operations</small></span></div>
      <div className="side-label">WORKSPACE</div>
      <button className={page==="dashboard"?"nav active":"nav"} onClick={()=>setPage("dashboard")}><LayoutDashboard size={18}/> Overview</button>
      <button className={page==="issues"?"nav active":"nav"} onClick={()=>setPage("issues")}><ClipboardList size={18}/> Issue audit log</button>
      <div className="sidebar-bottom"><ShieldCheck size={16}/> Secure session enabled</div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div><span className="eyebrow">OPERATIONS / {page.toUpperCase()}</span><h1>{page==="dashboard"?"Executive dashboard":"Issue audit log"}</h1></div><div className="profile"><div className="avatar">{session.user?.full_name?.[0] || "U"}</div><div><strong>{session.user?.full_name}</strong><small>{session.user?.role?.replaceAll("_"," ")}</small></div><button className="icon-btn" title="Sign out" onClick={signOut}><LogOut size={18}/></button></div></header>
      {page==="dashboard" ? <Dashboard/> : <IssueLog/>}
      <footer>HemaTrack · Person 4 implementation <span>Educational demo — verify all clinical decisions independently</span></footer>
    </main>
  </div>;
}
