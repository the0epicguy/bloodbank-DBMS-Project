import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Search, RefreshCw, ClipboardList, AlertCircle, Zap, Clock, CheckCircle2, Hospital } from "lucide-react";
import FulfillRequestModal from "./FulfillRequestModal";

interface Issue {
  issue_id: number;
  request_id: number;
  bank_id: number;
  unit_id: number;
  issue_date: string;
  blood_group: string;
  component_type: string;
  bank_name: string;
  hospital_name: string;
  recipient_name: string;
  urgency: string;
  notes?: string | null;
}

interface OpenRequest {
  request_id: number;
  hospital_id: number;
  hospital_name: string;
  recipient_id: number;
  recipient_name: string;
  blood_group: string;
  component_type: string;
  quantity: number;
  issued_units: number;
  remaining_units: number;
  urgency: string;
  status: string;
  request_date: string;
  notes?: string | null;
}

export default function IssueLog() {
  const [rows, setRows] = useState<Issue[]>([]);
  const [openRequests, setOpenRequests] = useState<OpenRequest[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState<OpenRequest | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [issuesData, requestsData] = await Promise.all([
        api<Issue[]>("/issues?limit=250"),
        api<OpenRequest[]>("/requests/open").catch(() => [] as OpenRequest[])
      ]);
      setRows(issuesData);
      setOpenRequests(requestsData);
    } catch (e: any) {
      setError(e.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const filtered = rows.filter(r =>
    [r.issue_id, r.request_id, r.bank_name, r.hospital_name, r.recipient_name, r.blood_group, r.component_type]
      .join(" ")
      .toLowerCase()
      .includes(query.toLowerCase())
  );

  return (
    <section className="content">
      {/* Open Requests section: allows testing FEFO Fulfillment! */}
      <div className="section-heading">
        <div>
          <h2>Hospital Fulfillment Queue</h2>
          <p>Triage and allocate compatible units to active patient requests.</p>
        </div>
        <button className="secondary-btn" onClick={() => void load()}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {openRequests.length > 0 ? (
        <div className="open-requests-grid">
          {openRequests.map(req => (
            <div key={req.request_id} className={`request-card ${req.urgency.toLowerCase()}`}>
              <div className="request-card-top">
                <span className={`urgency ${req.urgency.toLowerCase()}`}>
                  {req.urgency === "EMERGENCY" && <span className="live-dot" />}
                  {req.urgency}
                </span>
                <span className="request-id-badge">REQ #{req.request_id}</span>
              </div>
              <div className="request-card-body">
                <div className="req-group-row">
                  <span className={`blood-group ${req.blood_group.includes("-") ? "negative" : ""}`}>
                    {req.blood_group}
                  </span>
                  <div>
                    <strong>{req.component_type}</strong>
                    <small className="muted">{req.quantity} Unit(s) Demanded</small>
                  </div>
                </div>
                <div className="req-patient-info">
                  <strong>{req.recipient_name}</strong>
                  <small><Hospital size={12} /> {req.hospital_name}</small>
                </div>
                <div className="req-progress-info">
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${Math.min(100, (req.issued_units / req.quantity) * 100)}%` }}
                    />
                  </div>
                  <div className="req-progress-text">
                    <small>{req.issued_units} of {req.quantity} fulfilled</small>
                    <small className="remaining-text">
                      {req.remaining_units} remaining
                    </small>
                  </div>
                </div>
              </div>
              <button
                className="primary-btn full small-btn"
                onClick={() => setSelectedRequest(req)}
              >
                <Zap size={14} /> Fulfill Request (FEFO)
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-requests-banner">
          <CheckCircle2 size={20} className="text-green" />
          <span>All active patient requests are currently fulfilled. New requests will appear here immediately.</span>
        </div>
      )}

      {/* Issue Audit Log */}
      <div className="section-heading" style={{ marginTop: "2.5rem" }}>
        <div>
          <h2>Issued Blood Units Audit Log</h2>
          <p>Immutable relational log linking blood units, recipient, hospital, and issue timestamp.</p>
        </div>
      </div>

      <div className="toolbar">
        <div className="search">
          <Search size={17} />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search issue ID, recipient, hospital, blood group..."
          />
        </div>
        <span className="result-count">{filtered.length} audit records</span>
      </div>

      {error && (
        <div className="error-box">
          <AlertCircle size={17} />
          {error}
        </div>
      )}

      <div className="table-card">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ISSUE ID</th>
                <th>UNIT / GROUP</th>
                <th>RECIPIENT & HOSPITAL</th>
                <th>STORAGE BANK</th>
                <th>ISSUED TIMESTAMP</th>
                <th>URGENCY</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="empty">
                    Loading audit records...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty">
                    <ClipboardList size={28} />
                    <strong>No issue records found</strong>
                    <span>Records will appear here as soon as units are allocated.</span>
                  </td>
                </tr>
              ) : (
                filtered.map(r => (
                  <tr key={r.issue_id}>
                    <td>
                      <strong className="id-text">
                        #IS-{String(r.issue_id).padStart(4, "0")}
                      </strong>
                      <small>Request #{r.request_id}</small>
                    </td>
                    <td>
                      <div className="unit-cell">
                        <span className={`blood-group small ${r.blood_group.includes("-") ? "negative" : ""}`}>
                          {r.blood_group}
                        </span>
                        <div>
                          <strong>{r.component_type}</strong>
                          <small>
                            Bank {r.bank_id} / Unit {r.unit_id}
                          </small>
                        </div>
                      </div>
                    </td>
                    <td>
                      <strong>{r.recipient_name}</strong>
                      <small>{r.hospital_name}</small>
                    </td>
                    <td>{r.bank_name}</td>
                    <td>
                      {r.issue_date
                        ? new Date(r.issue_date).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      <span className={`urgency ${r.urgency?.toLowerCase()}`}>
                        {r.urgency}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      <p className="table-note">
        Audit log is read-only and backed by MySQL InnoDB foreign keys. Physical bags enforce the UNIQUE (bank_id, unit_id) constraint.
      </p>

      {/* FEFO Fulfillment Modal */}
      {selectedRequest && (
        <FulfillRequestModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onFulfilled={() => {
            void load();
          }}
        />
      )}
    </section>
  );
}
