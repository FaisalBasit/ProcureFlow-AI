# Band Setup Checklist

This project is only hackathon-ready when Band shows the ProcureFlow agents in a chat room and the app can post agent events there.

## What To Create In Band

Go to `https://app.band.ai/agents`, click **Connect Remote Agent**, and create these four required External Agents:

| Band agent name | Purpose | Paste API key into |
| --- | --- | --- |
| ProcureFlow Intake Agent | Parses and normalizes purchase requests | `BAND_INTAKE_API_KEY` |
| ProcureFlow Risk Agent | Scores vendor and spend risk | `BAND_RISK_API_KEY` |
| ProcureFlow Policy Agent | Checks procurement policy and can escalate/veto | `BAND_POLICY_API_KEY` |
| ProcureFlow Approval Agent | Creates human approval memo and final audit packet | `BAND_APPROVAL_API_KEY` |

For the strongest partner-prize demo, add this optional fifth External Agent:

| Band agent name | Purpose | Paste API key into |
| --- | --- | --- |
| ProcureFlow Featherless Review Agent | Posts the Featherless AI open-source second opinion before approval | `BAND_FEATHERLESS_REVIEW_API_KEY` |

Use these descriptions:

- **ProcureFlow Intake Agent:** Extracts vendor, amount, category, and business justification, then hands the structured request to the risk analyst.
- **ProcureFlow Risk Agent:** Evaluates vendor and transaction risk, reports concerns, and hands risk context to policy review.
- **ProcureFlow Policy Agent:** Applies procurement controls, decides whether the request is compliant, flagged, or blocked, and hands review context to approval.
- **ProcureFlow Featherless Review Agent:** Runs or reports an independent open-source model review through Featherless AI before the final approval memo.
- **ProcureFlow Approval Agent:** Summarizes all agent findings, requests human sign-off, and records the final tamper-evident audit hash.

Band displays each Agent API key only once. Copy each key immediately.

## Required `.env`

```env
BAND_ROOM_ID=your_band_chat_room_id_here
BAND_INTAKE_API_KEY=key_from_procureflow_intake_agent
BAND_RISK_API_KEY=key_from_procureflow_risk_agent
BAND_POLICY_API_KEY=key_from_procureflow_policy_agent
BAND_FEATHERLESS_REVIEW_API_KEY=optional_key_from_procureflow_featherless_review_agent
BAND_APPROVAL_API_KEY=key_from_procureflow_approval_agent

AI_PROVIDER=aimlapi
AIMLAPI_KEY=your_aimlapi_key
FEATHERLESS_API_KEY=your_featherless_key
OPENROUTER_API_KEY=optional_fallback_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_or_project_key
```

`BAND_API_KEY` is optional when all four per-agent keys are present. If `BAND_FEATHERLESS_REVIEW_API_KEY` is missing, the backend still runs the Featherless review step and attaches the result through the existing PolicyAgent-to-ApprovalAgent flow.

## Chat Room Wiring

1. Go to **Chats** in Band.
2. Create or open the demo chat room.
3. Add all four required ProcureFlow remote agents as participants.
4. Optionally add `ProcureFlow Featherless Review Agent` as a fifth participant.
5. Copy the chat room UUID from the URL or room settings into `BAND_ROOM_ID`.
6. Restart the FastAPI backend.

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

With the optional Featherless Band agent, `participant_count` should be 5 and `optional_partner_agent_configured` should be `true`.

Then submit a fresh purchase request. In Band/API context, the room should show events and directed handoffs from:

1. IntakeAgent: purchase request
2. IntakeAgent mentions RiskAgent
3. RiskAgent: risk report
4. RiskAgent mentions PolicyAgent
5. PolicyAgent: policy verdict
6. Featherless review: open-source second opinion
7. PolicyAgent or FeatherlessReviewAgent mentions ApprovalAgent
8. ApprovalAgent: approval summary
9. ApprovalAgent: final decision after human approval

In the app, the Audit Packet should also show `BandBridge` entries:

- `band_event_posted` for task/tool-result records
- `band_handoff_posted` for directed @mention handoffs

If credentials are wrong, those entries say `band_event_failed` with the exact Band error.

## Winning Demo Sequence

Show these moments in your video:

1. Band Agents page with four required ProcureFlow agents, plus Featherless review agent if configured.
2. Band chat room with agents as participants.
3. Submit page: enter a realistic request, such as a SaaS monitoring purchase.
4. Band room/context: show each agent event and @mention handoff appearing as the pipeline advances.
5. Dashboard: show status becomes `awaiting approval`, not stuck at `pending`.
6. Approvals page: show AI/ML risk analysis, policy verdict, Featherless review, approval memo, and human sign-off.
7. Audit Packet: show final status, agent log, `BandBridge` proof, and SHA-256 hash.

## Why This Satisfies The Requirement

Band is not only a notification sink. Each specialized agent uses its own Band Agent API key and posts its handoff/result into the shared Band room as a separate participant. The shared Band room becomes the coordination surface judges can inspect live, while Supabase preserves the enterprise audit trail.
