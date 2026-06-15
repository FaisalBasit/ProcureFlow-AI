"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestSummary {
  id: string;
  vendor_name: string;
  amount: number;
  category: string;
  status: string;
  justification: string;
  created_at: string;
}

export default function ApprovePage() {
  const [requests, setRequests] = useState<RequestSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [approverName, setApproverName] = useState("");
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const fetchPendingRequests = async () => {
    try {
      const res = await fetch(
        `${API_URL}/api/procurement/requests?status=awaiting_approval`
      );
      if (res.ok) {
        const data = await res.json();
        setRequests(data.requests || []);
      }
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingRequests();
    const interval = setInterval(fetchPendingRequests, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (requestId: string, approved: boolean) => {
    if (!approverName.trim()) {
      setMessage({
        type: "error",
        text: "Please enter your name to sign the decision.",
      });
      return;
    }

    setActionLoading(requestId);
    setMessage(null);

    try {
      const res = await fetch(`${API_URL}/api/procurement/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: requestId,
          approved,
          signed_by: approverName.trim(),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to submit decision");
      }

      const result = await res.json();
      setMessage({
        type: "success",
        text: `Request ${approved ? "approved" : "rejected"} successfully! SHA-256 audit hash: ${result.audit_packet?.audit_hash?.substring(0, 16)}...`,
      });

      // Remove from list
      setRequests((prev) => prev.filter((r) => r.id !== requestId));
    } catch (err: unknown) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "An error occurred",
      });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div>
      <div className="card">
        <h2 className="card-title">✋ Human Approval Required</h2>
        <p style={{ color: "var(--text-muted)", marginBottom: 16 }}>
          Review the agent analysis below and approve or reject each request.
          Your decision will be sealed with a SHA-256 audit hash.
        </p>

        <div className="form-group">
          <label className="form-label" htmlFor="approverName">
            Your Name (for audit signature)
          </label>
          <input
            id="approverName"
            className="form-input"
            type="text"
            placeholder="e.g., John Manager"
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
            style={{ maxWidth: 400 }}
          />
        </div>
      </div>

      {message && (
        <div className={`alert alert-${message.type}`}>{message.text}</div>
      )}

      {loading ? (
        <div className="loading">
          <span className="spinner" />
          Loading pending approvals...
        </div>
      ) : requests.length === 0 ? (
        <div className="card">
          <div style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
            <p style={{ fontSize: "2rem", marginBottom: 8 }}>✅</p>
            <p>No requests pending approval.</p>
            <p style={{ fontSize: "0.9rem", marginTop: 8 }}>
              All caught up! New requests requiring approval will appear here automatically.
            </p>
          </div>
        </div>
      ) : (
        requests.map((req) => (
          <div key={req.id} className="card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                marginBottom: 16,
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: "1.1rem" }}>
                  {req.vendor_name}
                </h3>
                <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
                  {req.category} · ${req.amount.toLocaleString()}
                </p>
              </div>
              <span className="badge badge-pending">Awaiting Approval</span>
            </div>

            <div
              className="alert alert-info"
              style={{ fontSize: "0.9rem", marginBottom: 16 }}
            >
              <strong>Justification:</strong> {req.justification}
            </div>

            <div
              style={{
                display: "flex",
                gap: 12,
                justifyContent: "flex-end",
                borderTop: "1px solid var(--border)",
                paddingTop: 16,
              }}
            >
              <button
                className="btn btn-danger"
                disabled={actionLoading === req.id}
                onClick={() => handleDecision(req.id, false)}
              >
                {actionLoading === req.id ? "Processing..." : "❌ Reject"}
              </button>
              <button
                className="btn btn-success"
                disabled={actionLoading === req.id}
                onClick={() => handleDecision(req.id, true)}
              >
                {actionLoading === req.id ? "Processing..." : "✅ Approve"}
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}