"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchJson } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_INTERVAL_MS = 10000;
const APPROVAL_STATUSES = new Set([
  "awaiting_approval",
  "pending_approval",
  "flagged_for_review",
]);

interface RequestSummary {
  id: string;
  vendor_name: string;
  amount: number;
  category: string;
  status: string;
  justification: string;
  created_at: string;
}

interface AgentLog {
  id: string;
  agent_name: string;
  action: string;
  output: Record<string, unknown> | string | null;
  created_at: string;
}

interface ApprovalRequest extends RequestSummary {
  agent_logs: AgentLog[];
  decision: Record<string, unknown> | null;
}

function normalizeOutput(output: AgentLog["output"]): Record<string, unknown> {
  if (!output) return {};
  if (typeof output === "string") {
    try {
      const parsed = JSON.parse(output);
      return typeof parsed === "object" && parsed ? parsed : {};
    } catch {
      return { raw: output };
    }
  }
  return output;
}

function latestOutput(
  logs: AgentLog[],
  agentName: string,
  action?: string
): Record<string, unknown> {
  const matches = logs.filter(
    (log) =>
      log.agent_name === agentName && (!action || log.action === action)
  );
  return normalizeOutput(matches[matches.length - 1]?.output ?? null);
}

function isReadyForApproval(req: ApprovalRequest): boolean {
  if (req.decision) return false;
  if (APPROVAL_STATUSES.has(req.status)) return true;
  return req.agent_logs.some(
    (log) =>
      log.agent_name === "ApprovalAgent" &&
      log.action === "approval_summary_generated"
  );
}

function toText(value: unknown, fallback = "Not available"): string {
  if (typeof value === "string" && value.trim()) {
    const cleaned = value
      .trim()
      .replace(/^```(?:json)?/i, "")
      .replace(/```$/, "")
      .trim();

    if (cleaned.startsWith("{")) {
      try {
        const parsed = JSON.parse(cleaned);
        if (typeof parsed.recommendation === "string") return parsed.recommendation;
        if (typeof parsed.notes === "string") return parsed.notes;
      } catch {
        return value;
      }
    }

    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function providerText(output: Record<string, unknown>): string {
  const provider = output.model_provider;
  if (!provider || typeof provider !== "object") return "";
  const meta = provider as Record<string, unknown>;
  const name = typeof meta.provider === "string" ? meta.provider : "";
  const model = typeof meta.model === "string" ? meta.model : "";
  if (!name && !model) return "";
  return [name, model].filter(Boolean).join(" / ");
}

function stripMarkdown(value: string): string {
  return value
    .replace(/\*\*/g, "")
    .replace(/^- /, "")
    .trim();
}

function FormattedSummary({ text }: { text: string }) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return <span>Approval summary is still being generated.</span>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {lines.map((line, index) => {
        const clean = stripMarkdown(line);
        const isHeading =
          line.startsWith("**") ||
          clean.endsWith(":") ||
          clean.toLowerCase().includes("summary");
        const isBullet = line.startsWith("- ");

        if (isHeading) {
          return (
            <strong key={`${clean}-${index}`} style={{ color: "var(--text)" }}>
              {clean.replace(/:$/, "")}
            </strong>
          );
        }

        return (
          <div
            key={`${clean}-${index}`}
            style={{
              color: "var(--text-muted)",
              paddingLeft: isBullet ? 12 : 0,
              borderLeft: isBullet ? "2px solid var(--border)" : "none",
            }}
          >
            {clean}
          </div>
        );
      })}
    </div>
  );
}

export default function ApprovePage() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [approverName, setApproverName] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const pendingFetchInFlight = useRef(false);

  const fetchPendingRequests = useCallback(async () => {
    if (pendingFetchInFlight.current) return;

    pendingFetchInFlight.current = true;
    try {
      const data = await fetchJson<{ requests: ApprovalRequest[] }>(
        `${API_URL}/api/procurement/requests/pending-approvals`
      );
      setRequests((data.requests || []).filter(isReadyForApproval));
      setLoadError(null);
    } catch (err: unknown) {
      setLoadError(
        err instanceof Error ? err.message : "Failed to load pending approvals"
      );
    } finally {
      pendingFetchInFlight.current = false;
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPendingRequests();
    const interval = setInterval(fetchPendingRequests, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchPendingRequests]);

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
      const result = await fetchJson<{ audit_packet?: { audit_hash?: string } }>(
        `${API_URL}/api/procurement/approve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: requestId,
            approved,
            signed_by: approverName.trim(),
          }),
        }
      );
      setMessage({
        type: "success",
        text: `Request ${approved ? "approved" : "rejected"} successfully. SHA-256 audit hash: ${result.audit_packet?.audit_hash?.substring(0, 16)}...`,
      });

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
        <h2 className="card-title">Human Approval Required</h2>
        <p style={{ color: "var(--text-muted)", marginBottom: 16 }}>
          Review the full agent analysis, then approve or reject. The decision
          is sealed with a SHA-256 audit hash.
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

      {loadError && (
        <div className="alert alert-error">
          <strong>Unable to load pending approvals:</strong> {loadError}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <span className="spinner" />
          Loading pending approvals...
        </div>
      ) : requests.length === 0 ? (
        <div className="card">
          <div style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
            <p>No requests pending approval.</p>
            <p style={{ fontSize: "0.9rem", marginTop: 8 }}>
              New requests requiring approval will appear here automatically.
            </p>
          </div>
        </div>
      ) : (
        requests.map((req) => {
          const risk = latestOutput(req.agent_logs, "RiskAgent");
          const policy = latestOutput(req.agent_logs, "PolicyAgent");
          const openSourceReview = latestOutput(
            req.agent_logs,
            "FeatherlessReviewAgent"
          );
          const approval = latestOutput(
            req.agent_logs,
            "ApprovalAgent",
            "approval_summary_generated"
          );

          return (
            <div key={req.id} className="card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: 16,
                  marginBottom: 16,
                }}
              >
                <div>
                  <h3 style={{ margin: 0, fontSize: "1.1rem" }}>
                    {req.vendor_name}
                  </h3>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
                    {req.category} | ${req.amount.toLocaleString()} | {req.id}
                  </p>
                </div>
                <span className="badge badge-pending">Awaiting Approval</span>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: 16,
                  marginBottom: 16,
                }}
              >
                <div className="alert alert-info" style={{ marginBottom: 0 }}>
                  <strong>Risk:</strong> {toText(risk.risk_level)}{" "}
                  {risk.risk_score ? `(${risk.risk_score}/10)` : ""}
                  <br />
                  <small>{toText(risk.recommendation, "No risk recommendation recorded.")}</small>
                  {providerText(risk) && (
                    <>
                      <br />
                      <small>Model: {providerText(risk)}</small>
                    </>
                  )}
                </div>
                <div className="alert alert-info" style={{ marginBottom: 0 }}>
                  <strong>Policy:</strong> {toText(policy.verdict)}
                  <br />
                  <small>{toText(policy.notes, "No policy notes recorded.")}</small>
                  {providerText(policy) && (
                    <>
                      <br />
                      <small>Model: {providerText(policy)}</small>
                    </>
                  )}
                </div>
                <div className="alert alert-info" style={{ marginBottom: 0 }}>
                  <strong>Open-source review:</strong>{" "}
                  {toText(openSourceReview.review_verdict, "Pending")}
                  {openSourceReview.confidence !== undefined
                    ? ` (${toText(openSourceReview.confidence)} confidence)`
                    : ""}
                  <br />
                  <small>
                    {toText(
                      openSourceReview.recommendation,
                      "Featherless review is pending or not configured."
                    )}
                  </small>
                  {providerText(openSourceReview) && (
                    <>
                      <br />
                      <small>Model: {providerText(openSourceReview)}</small>
                    </>
                  )}
                </div>
              </div>

              <div
                className="alert alert-info"
                style={{ marginBottom: 16 }}
              >
                <strong>Approval summary:</strong>
                <br />
                <FormattedSummary
                  text={toText(
                    approval.summary,
                    "Approval summary is still being generated."
                  )}
                />
              </div>

              <div
                className="alert alert-info"
                style={{ fontSize: "0.9rem", marginBottom: 16 }}
              >
                <strong>Business justification:</strong> {req.justification}
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
                  {actionLoading === req.id ? "Processing..." : "Reject"}
                </button>
                <button
                  className="btn btn-success"
                  disabled={actionLoading === req.id}
                  onClick={() => handleDecision(req.id, true)}
                >
                  {actionLoading === req.id ? "Processing..." : "Approve"}
                </button>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
