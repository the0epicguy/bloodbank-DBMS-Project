import { useState } from "react";
import { HeartPulse, ShieldCheck, ArrowRight, UserRound, Building2, Hospital, Droplet } from "lucide-react";
import { login, demoLogin } from "../../api/client";

const roles = [
  { role:"ADMIN", label:"Administrator", icon: ShieldCheck, desc:"System oversight" },
  { role:"BANK_STAFF", label:"Blood bank staff", icon: Droplet, desc:"Inventory & issue allocation" },
  { role:"HOSPITAL_STAFF", label:"Hospital staff", icon: Hospital, desc:"Requests & fulfillment" },
  { role:"DONOR", label:"Donor", icon: UserRound, desc:"Donor portal" },
];
export default function LoginPage({ onLogin }: { onLogin: (data:any)=>void }) {
  const [username,setUsername] = useState(""); const [password,setPassword] = useState("");
  const [error,setError] = useState(""); const [busy,setBusy] = useState(false);
  async function run(action:()=>Promise<any>) { setBusy(true); setError(""); try { onLogin(await action()); } catch(e:any) { setError(e.message || "Unable to sign in"); } finally { setBusy(false); } }
  return <div className="login-page">
    <div className="login-art"><div className="orb orb-one"/><div className="orb orb-two"/><div className="art-content"><div className="brand brand-large"><span className="brand-icon"><HeartPulse size={24}/></span><span>Hema<span className="brand-light">Track</span><small>Blood Bank Operations</small></span></div><div className="art-copy"><span className="pill"><span className="live-dot"/> CONNECTED CARE</span><h1>Every unit.<br/><em>Every life.</em></h1><p>A unified workspace for secure blood inventory, issue traceability, and hospital fulfillment.</p><div className="art-stat"><div className="stat-icon"><ShieldCheck/></div><div><strong>Account-protected access</strong><span>Role-aware session controls</span></div></div></div><div className="art-foot">BUILT FOR BETTER COORDINATION <span>✳</span></div></div></div>
    <div className="login-panel"><div className="login-form-wrap"><span className="eyebrow">WELCOME BACK</span><h2>Sign in to your workspace</h2><p className="muted">Use your assigned credentials or a demo role.</p>
      <form onSubmit={e=>{e.preventDefault();void run(()=>login(username,password));}}>
        <label>Username</label><input value={username} onChange={e=>setUsername(e.target.value)} placeholder="Enter your username" autoComplete="username" required/>
        <label>Password</label><input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="Enter your password" autoComplete="current-password" required/>
        {error && <div className="error-box">{error}</div>}<button className="primary-btn full" disabled={busy}>{busy?"Signing in…":"Sign in"} <ArrowRight size={17}/></button>
      </form>
      <div className="separator"><span/>OR QUICK DEMO LOGIN<span/></div>
      <div className="demo-grid">{roles.map(r=>{const Icon=r.icon;return <button className="demo-card" key={r.role} disabled={busy} onClick={()=>void run(()=>demoLogin(r.role))}><span className="demo-icon"><Icon size={18}/></span><span><strong>{r.label}</strong><small>{r.desc}</small></span><ArrowRight className="demo-arrow" size={15}/></button>})}</div>
      <div className="secure-note"><ShieldCheck size={16}/> Encrypted token session <span>•</span> Role-based access</div>
    </div><div className="login-copyright">© HemaTrack · Blood Bank Management System</div></div>
  </div>;
}
