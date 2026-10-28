import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Droplet, CheckCircle2, Clock3, TrendingUp, AlertTriangle, RefreshCw } from "lucide-react";
type Stock={blood_group:string;component_type:string;available_units:number};
type Metrics={total_requests:number;fulfilled_requests:number;fulfillment_pct:number;by_urgency:{urgency:string;total_requests:number;fulfilled_requests:number;fulfillment_pct:number}[]};
type Expiring={bank_id:number;bank_name:string;unit_id:number;blood_group:string;component_type:string;expiry_date:string;days_to_expiry:number};
export default function ExecutiveDashboard(){
 const [stock,setStock]=useState<Stock[]>([]);const [metrics,setMetrics]=useState<Metrics|null>(null);const [expiring,setExpiring]=useState<Expiring[]>([]);const [error,setError]=useState("");const [loading,setLoading]=useState(true);
 async function load(){setLoading(true);setError("");try{const [s,m,e]=await Promise.all([api<Stock[]>("/reports/stock-distribution"),api<Metrics>("/reports/fulfillment-metrics"),api<Expiring[]>("/reports/expiring-soon?days=7")]);setStock(s);setMetrics(m);setExpiring(e);}catch(e:any){setError(e.message);}finally{setLoading(false);}}
 useEffect(()=>{void load();},[]);
 const totalStock=stock.reduce((n,s)=>n+s.available_units,0);
 const groups=["O-","O+","A-","A+","B-","B+","AB-","AB+"];
 return <section className="content">
   <div className="welcome-banner"><div><span className="pill light-pill">LIVE OPERATIONS SNAPSHOT</span><h2>Clarity when every second counts.</h2><p>Monitor available stock, request fulfillment, and units nearing expiry.</p></div><div className="banner-mark"><Droplet size={70}/></div></div>
   {error&&<div className="error-box"><AlertTriangle size={17}/>{error}<button onClick={()=>void load()}>Retry</button></div>}
   <div className="section-heading"><div><h2>Operational overview</h2><p>Current data from the connected blood bank database.</p></div><button className="secondary-btn" onClick={()=>void load()}><RefreshCw size={15}/> Refresh</button></div>
   <div className="metric-grid">
    <Metric title="Available units" value={loading?"—":totalStock} hint="Unexpired units in stock" icon={<Droplet/>} tone="red"/>
    <Metric title="Total requests" value={loading?"—":metrics?.total_requests??0} hint="All recorded requests" icon={<Clock3/>} tone="amber"/>
    <Metric title="Fulfilled requests" value={loading?"—":metrics?.fulfilled_requests??0} hint="Fully allocated requests" icon={<CheckCircle2/>} tone="green"/>
    <Metric title="Fulfillment rate" value={loading?"—":`${metrics?.fulfillment_pct??0}%`} hint="Requests fully fulfilled" icon={<TrendingUp/>} tone="blue"/>
   </div>
   <div className="dashboard-grid">
    <div className="panel"><div className="panel-heading"><div><h3>Stock distribution</h3><p>Available units by blood group</p></div><span className="subtle-tag">IN STOCK</span></div>
      {loading?<div className="loading-line">Loading stock…</div>:<div className="stock-list">{groups.map(g=>{const count=stock.filter(s=>s.blood_group===g).reduce((n,s)=>n+s.available_units,0);const pct=totalStock?Math.round(count/totalStock*100):0;return <div className="stock-row" key={g}><span className={`blood-group ${g.includes("-")?"negative":""}`}>{g}</span><div className="stock-bar"><span style={{width:`${pct}%`}}/></div><strong>{count}</strong></div>})}</div>}
    </div>
    <div className="panel"><div className="panel-heading"><div><h3>Fulfillment by urgency</h3><p>Fully fulfilled requests</p></div></div>
      {loading?<div className="loading-line">Loading metrics…</div>:!metrics?.by_urgency.length?<div className="empty compact">No request metrics available yet.</div>:<div className="urgency-list">{["EMERGENCY","URGENT","ROUTINE"].map(level=>{const m=metrics.by_urgency.find(x=>x.urgency===level);return <div className="urgency-item" key={level}><div className="urgency-title"><span className={`urgency ${level.toLowerCase()}`}>{level}</span><strong>{m?.fulfilled_requests??0}<small> / {m?.total_requests??0}</small></strong></div><div className="progress"><span className={level.toLowerCase()} style={{width:`${m?.fulfillment_pct??0}%`}}/></div><small className="muted">{m?.fulfillment_pct??0}% fulfilled</small></div>})}</div>}
    </div>
   </div>
   <div className="panel expiring-panel"><div className="panel-heading"><div><h3><AlertTriangle size={18}/> Expiring within 7 days</h3><p>Prioritize safe stock rotation using FEFO.</p></div><span className="subtle-tag warning-tag">{expiring.length} UNITS</span></div>
    {loading?<div className="loading-line">Loading expiry alerts…</div>:expiring.length===0?<div className="empty compact">No available units are expiring in the next 7 days.</div>:<div className="expiry-list">{expiring.slice(0,8).map(u=><div className="expiry-row" key={`${u.bank_id}-${u.unit_id}`}><span className="blood-icon">✚</span><div className="expiry-main"><strong>{u.blood_group} · {u.component_type}</strong><small>{u.bank_name} · Unit {u.unit_id}</small></div><div className="expiry-date"><strong>{u.days_to_expiry===0?"Today":`${u.days_to_expiry} days`}</strong><small>{u.expiry_date}</small></div></div>)}</div>}
   </div>
 </section>
}
function Metric({title,value,hint,icon,tone}:{title:string;value:string|number;hint:string;icon:any;tone:string}){return <div className="metric-card"><div className={`metric-icon ${tone}`}>{icon}</div><span>{title}</span><strong>{value}</strong><small>{hint}</small></div>}
