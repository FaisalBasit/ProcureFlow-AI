"use client";

interface AuditPacketProps {
  request: Record<string, unknown>;
  decision: Record<string, unknown> | null;
  agentLogs: Record<string, unknown>[];
  onBack?: () => void;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "Not available";
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function asText(value: unknown, fallback = "Not available"): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function asNumber(value: unknown): number {
  if (typeof value === "number") return value;
  if (typeof value === "string") return Number(value) || 0;
  return 0;
}

function normalizeOutput(value: unknown): Record<string, unknown> {
  if (!value) return {};
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return typeof parsed === "object" && parsed ? parsed as Record<string, unknown> : {};
    } catch {
      return { raw: value };
    }
  }
  return typeof value === "object" ? value as Record<string, unknown> : {};
}

function latestOutput(
  logs: Record<string, unknown>[],
  agentName: string,
): Record<string, unknown> {
  const matches = logs.filter((log) => log.agent_name === agentName);
  return normalizeOutput(matches[matches.length - 1]?.output);
}

export default function AuditPacket({
  request,
  decision,
  agentLogs,
  onBack,
}: AuditPacketProps) {
  const status = asText(request.status, "pending");
  const auditHash = asText(decision?.audit_hash, "");
  const humanApproved = decision?.human_approved === true;
  const risk = latestOutput(agentLogs, "RiskAgent");
  const policy = latestOutput(agentLogs, "PolicyAgent");
  const openSourceReview = latestOutput(agentLogs, "FeatherlessReviewAgent");

  return (
    <div>
      {onBack && (
        <button
          className="btn btn-sm"
          style={{
            marginBottom: 16,
            backgroundColor: "var(--bg-input)",
            color: "var(--text)",
          }}
          onClick={onBack}
        >
          Back
        </button>
      )}

      <div className="card">
        <h2 className="card-title">Audit Packet</h2>

        {auditHash && (
          <div className="alert alert-info" style={{ wordBreak: "break-all" }}>
            <strong>SHA-256 Hash:</strong> {auditHash}
            <br />
            <small>
              This hash seals the integrity of this decision. Any tampering
              with the records will invalidate the hash.
            </small>
          </div>
        )}

        <div className="grid grid-2">
          <div>
            <h3
              style={{
                fontSize: "1rem",
                color: "var(--text-muted)",
                marginBottom: 12,
              }}
            >
              Request Details
            </h3>
            <table>
              <tbody>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Request ID</td>
                  <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                    {asText(request.id)}
                  </td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Vendor</td>
                  <td>{asText(request.vendor_name)}</td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Amount</td>
                  <td>${asNumber(request.amount).toLocaleString()}</td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Category</td>
                  <td>{asText(request.category)}</td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Status</td>
                  <td>
                    <span
                      className={`badge ${
                        status === "approved"
                          ? "badge-approved"
                          : status === "rejected" || status === "rejected_by_policy"
                          ? "badge-rejected"
                          : "badge-pending"
                      }`}
                    >
                      {status.replace(/_/g, " ")}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Created</td>
                  <td>{formatDate(asText(request.created_at, ""))}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div>
            <h3
              style={{
                fontSize: "1rem",
                color: "var(--text-muted)",
                marginBottom: 12,
              }}
            >
              Decision
            </h3>
            {decision ? (
              <table>
                <tbody>
                  <tr>
                    <td style={{ color: "var(--text-muted)" }}>Approved</td>
                    <td>
                      <span
                        className={`badge ${
                          humanApproved ? "badge-approved" : "badge-rejected"
                        }`}
                      >
                        {humanApproved ? "Approved" : "Rejected"}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td style={{ color: "var(--text-muted)" }}>Signed By</td>
                    <td>{asText(decision.signed_by)}</td>
                  </tr>
                  <tr>
                    <td style={{ color: "var(--text-muted)" }}>Decided At</td>
                    <td>{formatDate(asText(decision.decided_at, ""))}</td>
                  </tr>
                  <tr>
                    <td style={{ color: "var(--text-muted)" }}>Audit Hash</td>
                    <td
                      style={{
                        fontFamily: "monospace",
                        fontSize: "0.8rem",
                        wordBreak: "break-all",
                      }}
                    >
                      {auditHash}
                    </td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <p style={{ color: "var(--text-muted)" }}>
                No decision recorded yet.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Decision Evidence</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 16,
          }}
        >
          <div className="alert alert-info" style={{ marginBottom: 0 }}>
            <strong>AI/ML risk:</strong> {asText(risk.risk_level)}{" "}
            {risk.risk_score ? `(${asText(risk.risk_score)}/10)` : ""}
            <br />
            <small>{asText(risk.recommendation, "No risk recommendation recorded.")}</small>
          </div>
          <div className="alert alert-info" style={{ marginBottom: 0 }}>
            <strong>Policy verdict:</strong> {asText(policy.verdict)}
            <br />
            <small>{asText(policy.notes, "No policy notes recorded.")}</small>
          </div>
          <div className="alert alert-info" style={{ marginBottom: 0 }}>
            <strong>Featherless review:</strong>{" "}
            {asText(openSourceReview.review_verdict, "Pending")}
            <br />
            <small>
              {asText(
                openSourceReview.recommendation,
                "Open-source model review is pending or not configured."
              )}
            </small>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Agent Processing Log</h2>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Action</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {agentLogs.map((log) => (
                <tr key={asText(log.id)}>
                  <td>
                    <strong>{asText(log.agent_name)}</strong>
                  </td>
                  <td>{asText(log.action).replace(/_/g, " ")}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    {formatDate(asText(log.created_at, ""))}
                  </td>
                </tr>
              ))}
              {agentLogs.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ textAlign: "center", color: "var(--text-muted)" }}>
                    No agent activity recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
