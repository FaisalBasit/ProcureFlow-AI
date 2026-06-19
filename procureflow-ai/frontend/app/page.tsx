"use client";

import { useState } from "react";
import RequestForm from "@/components/RequestForm";
import AgentTimeline from "@/components/AgentTimeline";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AgentLog {
  id: string;
  agent_name: string;
  action: string;
  output: Record<string, unknown>;
  created_at: string;
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const submittedRequestId =
    typeof result?.request_id === "string" ? result.request_id : "";

  const handleSubmit = async (data: {
    vendor_name: string;
    amount: number;
    category: string;
    justification: string;
  }) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setRequestId(null);
    setLogs([]);

    try {
      const res = await fetch(`${API_URL}/api/procurement/submit-and-process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const response = await res.json();
      setRequestId(response.request_id);
      setResult(response);

      // Fetch initial logs
      const logsRes = await fetch(
        `${API_URL}/api/procurement/requests/${response.request_id}`
      );
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        if (logsData.agent_logs) {
          setLogs(logsData.agent_logs);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="grid grid-2">
        <div>
          <RequestForm onSubmit={handleSubmit} loading={loading} />
        </div>
        <div>
          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {result && !error && (
            <div className="card">
              <h2 className="card-title">✅ Request Submitted</h2>
              <div className="alert alert-success">
                Request <strong>#{submittedRequestId}</strong> has been submitted
                and is being processed by the agent pipeline.
              </div>

              {result && (
                <div style={{ marginTop: 12 }}>
                  <table>
                    <tbody>
                      <tr>
                        <td style={{ color: "var(--text-muted)" }}>Request ID</td>
                        <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                          {result.request_id as string}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ color: "var(--text-muted)" }}>Intake Status</td>
                        <td>{(result.intake as Record<string, unknown>)?.status as string}</td>
                      </tr>
                      <tr>
                        <td style={{ color: "var(--text-muted)" }}>Risk Assessment</td>
                        <td>{(result.risk_assessment as Record<string, unknown>)?.status as string}</td>
                      </tr>
                      <tr>
                        <td style={{ color: "var(--text-muted)" }}>Policy Check</td>
                        <td>{(result.policy_check as Record<string, unknown>)?.status as string}</td>
                      </tr>
                      <tr>
                        <td style={{ color: "var(--text-muted)" }}>Approval Status</td>
                        <td>
                          {(result.approval as Record<string, unknown>)?.status as string || "N/A"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {requestId && (
            <AgentTimeline requestId={requestId} logs={logs} />
          )}
        </div>
      </div>
    </div>
  );
}
