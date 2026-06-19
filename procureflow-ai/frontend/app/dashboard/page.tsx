"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AuditPacket from "@/components/AuditPacket";
import { fetchJson } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_INTERVAL_MS = 10000;

interface RequestSummary {
  id: string;
  vendor_name: string;
  amount: number;
  category: string;
  status: string;
  created_at: string;
}

export default function Dashboard() {
  const [requests, setRequests] = useState<RequestSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [auditData, setAuditData] = useState<Record<string, unknown> | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const requestInFlight = useRef(false);

  const fetchRequests = useCallback(async () => {
    if (requestInFlight.current) return;

    requestInFlight.current = true;
    try {
      const data = await fetchJson<{ requests: RequestSummary[] }>(
        `${API_URL}/api/procurement/requests${
          filter ? `?status=${filter}` : ""
        }`
      );
      setRequests(data.requests || []);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load requests");
    } finally {
      requestInFlight.current = false;
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchRequests();
    const interval = setInterval(fetchRequests, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchRequests]);

  const viewDetails = async (id: string) => {
    try {
      const data = await fetchJson<Record<string, unknown>>(
        `${API_URL}/api/procurement/requests/${id}`
      );
      setAuditData(data);
      setSelectedId(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load request details");
    }
  };

  const getStatusClass = (status: string) => {
    if (["approved"].includes(status)) return "badge-approved";
    if (["rejected", "rejected_by_policy"].includes(status)) return "badge-rejected";
    if (["pending", "risk_assessment", "policy_check", "awaiting_approval"].includes(status))
      return "badge-pending";
    return "badge-review";
  };

  if (selectedId && auditData) {
    return (
      <AuditPacket
        request={auditData.request as Record<string, unknown>}
        decision={auditData.decision as Record<string, unknown>}
        agentLogs={auditData.agent_logs as Record<string, unknown>[]}
        onBack={() => {
          setSelectedId(null);
          setAuditData(null);
        }}
      />
    );
  }

  return (
    <div>
      <div className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 16,
          }}
        >
          <h2 className="card-title" style={{ margin: 0 }}>
            Request Dashboard
          </h2>
          <div style={{ display: "flex", gap: 8 }}>
            <select
              className="form-select"
              style={{ width: "auto" }}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="awaiting_approval">Awaiting Approval</option>
              <option value="rejected_by_policy">Rejected by Policy</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="alert alert-error">
            <strong>Unable to load requests:</strong> {error}
          </div>
        )}

        {loading ? (
          <div className="loading">
            <span className="spinner" />
            Loading requests...
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr key={req.id}>
                    <td>
                      <strong>{req.vendor_name}</strong>
                    </td>
                    <td>${req.amount.toLocaleString()}</td>
                    <td>{req.category}</td>
                    <td>
                      <span className={`badge ${getStatusClass(req.status)}`}>
                        {req.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                      {new Date(req.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => viewDetails(req.id)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
                {requests.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      style={{
                        textAlign: "center",
                        color: "var(--text-muted)",
                        padding: 32,
                      }}
                    >
                      No purchase requests found.
                      <br />
                      <a
                        href="/"
                        style={{ color: "var(--primary)", marginTop: 8, display: "inline-block" }}
                      >
                        Submit your first request →
                      </a>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
