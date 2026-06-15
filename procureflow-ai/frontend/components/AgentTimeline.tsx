"use client";

import { useEffect, useState } from "react";

interface AgentLog {
  id: string;
  agent_name: string;
  action: string;
  output: Record<string, unknown>;
  created_at: string;
}

interface AgentTimelineProps {
  requestId: string;
  logs: AgentLog[];
}

const AGENT_ICONS: Record<string, string> = {
  IntakeAgent: "📥",
  RiskAgent: "⚠️",
  PolicyAgent: "📋",
  ApprovalAgent: "✅",
  WebhookRouter: "🔗",
};

const AGENT_COLORS: Record<string, "active" | "success" | "danger" | "warning"> = {
  IntakeAgent: "active",
  RiskAgent: "warning",
  PolicyAgent: "warning",
  ApprovalAgent: "success",
};

function formatAction(action: string): string {
  return action
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function AgentTimeline({ requestId, logs }: AgentTimelineProps) {
  const [currentLogs, setCurrentLogs] = useState<AgentLog[]>(logs);

  // Poll for new logs every 3 seconds if request is still processing
  useEffect(() => {
    if (!requestId) return;

    const isPending = currentLogs.some(
      (log) =>
        log.action.includes("pending") ||
        log.action.includes("submitted") ||
        log.action.includes("processing")
    );

    if (!isPending && currentLogs.length > 0) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/procurement/requests/${requestId}`
        );
        if (res.ok) {
          const data = await res.json();
          if (data.agent_logs) {
            setCurrentLogs(data.agent_logs);
          }
        }
      } catch {
        // Silently retry
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [requestId, currentLogs]);

  if (currentLogs.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">🔄 Agent Timeline</h2>
        <p style={{ color: "var(--text-muted)" }}>
          Waiting for agent activity...
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="card-title">🔄 Agent Timeline</h2>
      <div className="timeline">
        {currentLogs.map((log) => (
          <div key={log.id} className="timeline-item">
            <div
              className={`timeline-dot ${AGENT_COLORS[log.agent_name] || "active"}`}
            />
            <div className="timeline-content">
              <div className="timeline-agent">
                {AGENT_ICONS[log.agent_name] || "🤖"} {log.agent_name}
                <span
                  style={{
                    float: "right",
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                  }}
                >
                  {formatTime(log.created_at)}
                </span>
              </div>
              <div className="timeline-action">
                {formatAction(log.action)}
              </div>
              {log.output?.summary && (
                <div
                  style={{
                    marginTop: 8,
                    padding: 8,
                    backgroundColor: "var(--bg-card)",
                    borderRadius: "4px",
                    fontSize: "0.85rem",
                    color: "var(--text-muted)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {log.output.summary as string}
                </div>
              )}
              {log.output?.risk_level && (
                <div style={{ marginTop: 8 }}>
                  <span
                    className={`badge ${
                      log.output.risk_level === "low"
                        ? "badge-approved"
                        : log.output.risk_level === "high" || log.output.risk_level === "critical"
                        ? "badge-rejected"
                        : "badge-review"
                    }`}
                  >
                    Risk: {log.output.risk_level as string} ({log.output.risk_score as string}/10)
                  </span>
                </div>
              )}
              {log.output?.verdict && (
                <div style={{ marginTop: 8 }}>
                  <span
                    className={`badge ${
                      log.output.verdict === "approved"
                        ? "badge-approved"
                        : log.output.verdict === "rejected"
                        ? "badge-rejected"
                        : "badge-review"
                    }`}
                  >
                    {log.output.verdict as string}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}