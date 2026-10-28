import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { X, Zap, ShieldCheck, AlertTriangle, CheckCircle2, Droplet, Clock, ArrowRight } from "lucide-react";

interface CandidateUnit {
  bank_id: number;
  bank_name: string;
  unit_id: number;
  blood_group: string;
  component_type: string;
  volume_ml: number;
  expiry_date: string;
  days_to_expiry: number;
  is_exact_match: boolean;
}

interface RequestItem {
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

interface Props {
  request: RequestItem;
  onClose: () => void;
  onFulfilled: () => void;
}

export default function FulfillRequestModal({ request, onClose, onFulfilled }: Props) {
  const [candidates, setCandidates] = useState<CandidateUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [successResult, setSuccessResult] = useState<any>(null);

  useEffect(() => {
    async function loadCandidates() {
      setLoading(true);
      setError("");
      try {
        const units = await api<CandidateUnit[]>(`/requests/${request.request_id}/candidate-units`);
        setCandidates(units);
      } catch (err: any) {
        setError(err.message || "Failed to load candidate units");
      } finally {
        setLoading(false);
      }
    }
    loadCandidates();
  }, [request.request_id]);

  async function handleAutoFulfil() {
    setBusy(true);
    setError("");
    try {
      const res = await api<any>(`/requests/${request.request_id}/auto-fulfil`, {
        method: "POST"
      });
      setSuccessResult(res);
      onFulfilled();
    } catch (err: any) {
      setError(err.message || "Auto-fulfillment failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleManualIssue(unit: CandidateUnit) {
    setBusy(true);
    setError("");
    try {
      await api<any>("/issues/manual", {
        method: "POST",
        body: JSON.stringify({
          request_id: request.request_id,
          bank_id: unit.bank_id,
          unit_id: unit.unit_id,
          notes: "Allocated via Person 4 FEFO Interface"
        })
      });
      setSuccessResult({
        status: "ISSUED",
        issued_now: 1,
        allocated: [unit]
      });
      onFulfilled();
    } catch (err: any) {
      setError(err.message || "Manual unit issue failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-wrap">
            <span className={`urgency ${request.urgency.toLowerCase()}`}>
              {request.urgency}
            </span>
            <h3>Fulfill Request #{request.request_id}</h3>
          </div>
          <button className="icon-btn" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>

        {/* Request Summary Box */}
        <div className="request-summary-box">
          <div className="summary-item">
            <span className="summary-label">Patient / Recipient</span>
            <strong>{request.recipient_name}</strong>
            <small>{request.hospital_name}</small>
          </div>
          <div className="summary-item">
            <span className="summary-label">Required Component</span>
            <div className="group-badge-wrap">
              <span className={`blood-group ${request.blood_group.includes("-") ? "negative" : ""}`}>
                {request.blood_group}
              </span>
              <strong>{request.component_type}</strong>
            </div>
          </div>
          <div className="summary-item">
            <span className="summary-label">Fulfillment Status</span>
            <strong>
              {request.issued_units} / {request.quantity} units issued
            </strong>
            <small className="muted">{request.remaining_units} unit(s) remaining</small>
          </div>
        </div>

        {error && (
          <div className="error-box" style={{ margin: "1rem 0" }}>
            <AlertTriangle size={17} />
            <span>{error}</span>
          </div>
        )}

        {successResult ? (
          <div className="fulfillment-success-box">
            <div className="success-icon-wrap">
              <CheckCircle2 size={40} className="text-green" />
            </div>
            <h4>Allocation Successfully Recorded!</h4>
            <p>
              Status updated to <strong>{successResult.status}</strong>. {successResult.issued_now} unit(s)
              allocated and written to the audit log.
            </p>
            <div className="allocated-units-list">
              {successResult.allocated?.map((u: any, idx: number) => (
                <div key={idx} className="allocated-tag">
                  <Droplet size={14} />
                  <span>
                    Bank {u.bank_id} / Unit {u.unit_id} ({u.blood_group} {u.component_type})
                  </span>
                </div>
              ))}
            </div>
            <button className="primary-btn" onClick={onClose} style={{ marginTop: "1rem" }}>
              Done & Return to Log
            </button>
          </div>
        ) : (
          <>
            {/* Auto FEFO Action banner */}
            <div className="fefo-hero-action">
              <div>
                <div className="fefo-hero-title">
                  <Zap size={18} />
                  <strong>Automated FEFO Allocation Engine</strong>
                </div>
                <p>
                  Scans cold inventory, selects compatible bags ordered by earliest expiry (MySQL row-locked with SKIP LOCKED), and transitions request status.
                </p>
              </div>
              <button
                className="primary-btn pulse-on-hover"
                disabled={busy || loading || candidates.length === 0}
                onClick={handleAutoFulfil}
              >
                {busy ? "Allocating..." : "Execute 1-Click Auto-FEFO"}
              </button>
            </div>

            {/* Candidate Units Table */}
            <div className="candidate-section">
              <div className="candidate-header">
                <h4>
                  Candidate Compatible Units (FEFO Ordered)
                  <span className="badge-count">{candidates.length} Available</span>
                </h4>
                <small className="muted">Sorted by expiry date ascending (First-Expiry-First-Out)</small>
              </div>

              {loading ? (
                <div className="loading-line">Searching cold storage for compatible units...</div>
              ) : candidates.length === 0 ? (
                <div className="empty-candidate-box">
                  <AlertTriangle size={24} />
                  <strong>No compatible units in stock</strong>
                  <p>Check other blood banks or register new donations.</p>
                </div>
              ) : (
                <div className="candidate-table-wrap">
                  <table className="candidate-table">
                    <thead>
                      <tr>
                        <th>FEFO RANK</th>
                        <th>BLOOD GROUP</th>
                        <th>STORAGE CENTER</th>
                        <th>EXPIRY & ROTATION</th>
                        <th>ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {candidates.map((u, idx) => (
                        <tr key={`${u.bank_id}-${u.unit_id}`}>
                          <td>
                            <span className={`fefo-rank ${idx === 0 ? "rank-first" : ""}`}>
                              #{idx + 1} {idx === 0 && "★ PRIORITY"}
                            </span>
                          </td>
                          <td>
                            <div className="unit-cell">
                              <span className={`blood-group small ${u.blood_group.includes("-") ? "negative" : ""}`}>
                                {u.blood_group}
                              </span>
                              <div>
                                <strong>{u.component_type}</strong>
                                <small>
                                  {u.is_exact_match ? (
                                    <span className="match-exact">Exact Match</span>
                                  ) : (
                                    <span className="match-compatible">Cross-Compatible</span>
                                  )}
                                </small>
                              </div>
                            </div>
                          </td>
                          <td>
                            <strong>{u.bank_name}</strong>
                            <small className="muted">Unit #{u.unit_id} ({u.volume_ml} mL)</small>
                          </td>
                          <td>
                            <div className="expiry-indicator">
                              <span
                                className={`expiry-badge ${
                                  u.days_to_expiry <= 3 ? "critical" : u.days_to_expiry <= 7 ? "warning" : "ok"
                                }`}
                              >
                                <Clock size={12} />
                                {u.days_to_expiry <= 0 ? "Expires today!" : `In ${u.days_to_expiry} days`}
                              </span>
                              <small className="muted">{u.expiry_date}</small>
                            </div>
                          </td>
                          <td>
                            <button
                              className="secondary-btn small-btn"
                              disabled={busy}
                              onClick={() => handleManualIssue(u)}
                            >
                              Allocate Bag
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
