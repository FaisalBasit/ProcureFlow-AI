"use client";

import { useEffect, useState } from "react";

interface AgentLog {
  id: string;
  agent_name: string;
  action: string;
  output: Record<string, unknown> | string | null;
  created_at: string;
}

interface AgentTimelineProps {
  requestId: string;
  logs: AgentLog[];
}

const AGENT_LABELS: Record<string, string> = {
  IntakeAgent: "Intake",
  RiskAgent: "Risk",
  PolicyAgent: "Policy",
  ApprovalAgent: "Approval",
  WebhookRouter: "Router",
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

export default function AgentTimeline({ requestId, logs }: AgentTimelineProps) {
  const [currentLogs, setCurrentLogs] = useState<AgentLog[]>(logs);

  useEffect(() => {
    setCurrentLogs(logs);
  }, [logs]);

  useEffect(() => {
    if (!requestId) return;

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
        // Silently retry while the user watches the pipeline.
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [requestId]);

  if (currentLogs.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">Agent Timeline</h2>
        <p style={{ color: "var(--text-muted)" }}>
          Waiting for agent activity...
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="card-title">Agent Timeline</h2>
      <div className="timeline">
        {currentLogs.map((log) => {
          const output = normalizeOutput(log.output);
          const summary = typeof output.summary === "string" ? output.summary : "";
          const riskLevel = typeof output.risk_level === "string" ? output.risk_level : "";
          const riskScore =
            typeof output.risk_score === "number" || typeof output.risk_score === "string"
              ? String(output.risk_score)
              : "n/a";
          const verdict = typeof output.verdict === "string" ? output.verdict : "";

          return (
            <div key={log.id} className="timeline-item">
              <div
                className={`timeline-dot ${AGENT_COLORS[log.agent_name] || "active"}`}
              />
              <div className="timeline-content">
                <div className="timeline-agent">
                  {AGENT_LABELS[log.agent_name] || "Agent"}: {log.agent_name}
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
                <div className="timeline-action">{formatAction(log.action)}</div>

                {summary && (
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
                    {summary}
                  </div>
                )}

                {riskLevel && (
                  <div style={{ marginTop: 8 }}>
                    <span
                      className={`badge ${
                        riskLevel === "low"
                          ? "badge-approved"
                          : riskLevel === "high" || riskLevel === "critical"
                          ? "badge-rejected"
                          : "badge-review"
                      }`}
                    >
                      Risk: {riskLevel} ({riskScore}/10)
                    </span>
                  </div>
                )}

                {verdict && (
                  <div style={{ marginTop: 8 }}>
                    <span
                      className={`badge ${
                        verdict === "approved"
                          ? "badge-approved"
                          : verdict === "rejected"
                          ? "badge-rejected"
                          : "badge-review"
                      }`}
                    >
                      {verdict}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
