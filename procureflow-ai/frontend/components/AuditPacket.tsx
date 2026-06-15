"use client";

interface AuditPacketProps {
  request: Record<string, unknown>;
  decision: Record<string, unknown>;
  agentLogs: Record<string, unknown>[];
  onBack?: () => void;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function AuditPacket({
  request,
  decision,
  agentLogs,
  onBack,
}: AuditPacketProps) {
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
          ← Back
        </button>
      )}

      <div className="card">
        <h2 className="card-title">📄 Audit Packet</h2>

        {decision?.audit_hash && (
          <div
            className="alert alert-info"
            style={{ wordBreak: "break-all" }}
          >
            <strong>SHA-256 Hash:</strong> {decision.audit_hash as string}
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
                    {request.id as string}
                  </td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Vendor</td>
                  <td>{request.vendor_name as string}</td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Amount</td>
                  <td>
                    ${(request.amount as number).toLocaleString()}
                  </td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Category</td>
                  <td>{request.category as string}</td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Status</td>
                  <td>
                    <span
                      className={`badge ${
                        request.status === "approved"
                          ? "badge-approved"
                          : request.status === "rejected" ||
                            request.status === "rejected_by_policy"
                          ? "badge-rejected"
                          : "badge-pending"
                      }`}
                    >
                      {request.status as string}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td style={{ color: "var(--text-muted)" }}>Created</td>
                  <td>{formatDate(request.created_at as string)}</td>
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
                          decision.human_approved
                            ? "badge-approved"
                            : "badge-rejected"
                        }`}
                      >
                        {decision.human_approved ? "✅ Approved" : "❌ Rejected"}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td style={{ color: "var(--text-muted)" }}>Signed By</td>
                    <td>{decision.signed_by as string}</td>
                  </tr>
                  <tr>
                    <td style={{ color: "var(--text-muted)" }}>Decided At</td>
                    <td>{formatDate(decision.decided_at as string)}</td>
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
                      {decision.audit_hash as string}
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
        <h2 className="card-title">📋 Agent Processing Log</h2>
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
                <tr key={log.id as string}>
                  <td>
                    <strong>{log.agent_name as string}</strong>
                  </td>
                  <td>
                    {(log.action as string).replace(/_/g, " ")}
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    {formatDate(log.created_at as string)}
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