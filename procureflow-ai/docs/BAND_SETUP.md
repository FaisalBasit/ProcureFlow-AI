# Band Setup Checklist

This project is only hackathon-ready when Band shows the ProcureFlow agents in a chat room and the app can post agent events there.

## What To Create In Band

Go to `https://app.band.ai/agents`, click **Connect Remote Agent**, and create these four External Agents:

| Band agent name | Purpose | Paste API key into |
| --- | --- | --- |
| ProcureFlow Intake Agent | Parses and normalizes purchase requests | `BAND_INTAKE_API_KEY` |
| ProcureFlow Risk Agent | Scores vendor and spend risk | `BAND_RISK_API_KEY` |
| ProcureFlow Policy Agent | Checks procurement policy and can escalate/veto | `BAND_POLICY_API_KEY` |
| ProcureFlow Approval Agent | Creates human approval memo and final audit packet | `BAND_APPROVAL_API_KEY` |

Use these descriptions:

- **ProcureFlow Intake Agent:** Extracts vendor, amount, category, and business justification, then hands the structured request to the risk analyst.
- **ProcureFlow Risk Agent:** Evaluates vendor and transaction risk, reports concerns, and hands risk context to policy review.
- **ProcureFlow Policy Agent:** Applies procurement controls, decides whether the request is compliant, flagged, or blocked, and hands review context to approval.
- **ProcureFlow Approval Agent:** Summarizes all agent findings, requests human sign-off, and records the final tamper-evident audit hash.

Band displays each Agent API key only once. Copy each key immediately.

## Required `.env`

```env
BAND_ROOM_ID=your_band_chat_room_id_here
BAND_INTAKE_API_KEY=key_from_procureflow_intake_agent
BAND_RISK_API_KEY=key_from_procureflow_risk_agent
BAND_POLICY_API_KEY=key_from_procureflow_policy_agent
BAND_APPROVAL_API_KEY=key_from_procureflow_approval_agent

OPENROUTER_API_KEY=your_openrouter_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_or_project_key
```

`BAND_API_KEY` is optional when all four per-agent keys are present.

## Chat Room Wiring

1. Go to **Chats** in Band.
2. Create or open the demo chat room.
3. Add all four ProcureFlow remote agents as participants.
4. Copy the chat room UUID from the URL or room settings into `BAND_ROOM_ID`.
5. Restart the FastAPI backend.

The agents must be participants in the chat room. A valid Agent API key still returns `403 Forbidden` if that agent is not in `BAND_ROOM_ID`.

## Verify Before Recording

Run:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/procurement/band/status" -Method Get | ConvertTo-Json -Depth 8
```

You want:

```json
{
  "connected": true,
  "participant_count": 4
}
```

Then submit a fresh purchase request. In Band/API context, the room should show events and directed handoffs from:

1. IntakeAgent: purchase request
2. IntakeAgent mentions RiskAgent
3. RiskAgent: risk report
4. RiskAgent mentions PolicyAgent
5. PolicyAgent: policy verdict
6. PolicyAgent mentions ApprovalAgent
7. ApprovalAgent: approval summary
8. ApprovalAgent: final decision after human approval

In the app, the Audit Packet should also show `BandBridge` entries:

- `band_event_posted` for task/tool-result records
- `band_handoff_posted` for directed @mention handoffs

If credentials are wrong, those entries say `band_event_failed` with the exact Band error.

## Winning Demo Sequence

Show these moments in your video:

1. Band Agents page with four ProcureFlow agents.
2. Band chat room with all four agents as participants.
3. Submit page: enter a realistic request, such as a SaaS monitoring purchase.
4. Band room/context: show each agent event and @mention handoff appearing as the pipeline advances.
5. Dashboard: show status becomes `awaiting approval`, not stuck at `pending`.
6. Approvals page: show risk analysis, policy verdict, approval memo, and human sign-off.
7. Audit Packet: show final status, agent log, `BandBridge` proof, and SHA-256 hash.

## Why This Satisfies The Requirement

Band is not only a notification sink. Each specialized agent uses its own Band Agent API key and posts its handoff/result into the shared Band room as a separate participant. The shared Band room becomes the coordination surface judges can inspect live, while Supabase preserves the enterprise audit trail.
