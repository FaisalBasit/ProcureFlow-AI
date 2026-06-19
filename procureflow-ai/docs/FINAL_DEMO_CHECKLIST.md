# Final Demo Checklist

## What To Do Now

1. Do not spend more than a few minutes on expired/unavailable partner coupons.
2. Keep the four required Band agents working: Intake, Risk, Policy, Approval.
3. If you can get partner keys from dashboard, Discord, or support, add them and restart:

```env
AI_PROVIDER=aimlapi
AIMLAPI_KEY=your_aimlapi_key
FEATHERLESS_API_KEY=your_featherless_key
```

4. Optional but strong: create `ProcureFlow Featherless Review Agent` in Band, add it to the room, and set:

```env
BAND_FEATHERLESS_REVIEW_API_KEY=your_featherless_review_band_agent_key
```

The project still meets the main hackathon requirement with the four existing Band agents.

## Recording Flow

1. Show the problem: procurement approvals are slow, fragmented, and hard to audit.
2. Show Band Agents page with the four required ProcureFlow agents.
3. Show the Band chat room with the agents as participants.
4. Submit a realistic request:

```text
Vendor: Atlas Cloud Security
Amount: 18600
Category: software
Justification: Annual security monitoring and incident response coverage for production systems
```

5. Show the live Agent Timeline:
   - Intake parsed request
   - Risk analysis complete
   - Policy check complete
   - Open-source review complete or configuration required
   - Approval summary generated
6. Show the Band room/context with events and directed handoffs.
7. Show Approvals page with AI/ML risk, policy, Featherless review, approval summary, and signer field.
8. Approve as a human.
9. Show Audit Packet with final decision, agent log, BandBridge records, and SHA-256 hash.

## Judging Criteria Answer

Application of Technology: Band is inside the workflow. Agents use Band events and handoffs to pass state between specialized roles, not as a final notification channel.

Presentation: The UI has a clear enterprise flow: Submit, live timeline, Dashboard, Approvals, and Audit Packet. The demo can show each agent's role and result.

Business Value: Procurement approval is a real internal enterprise workflow. This reduces manual coordination, speeds review, and preserves traceability.

Originality: The project combines Band coordination, AI/ML API reasoning, Featherless open-source second review, human-in-the-loop approval, and SHA-256 audit sealing.

## Honest Partner-Prize Position

If `AIMLAPI_KEY` is set, RiskAgent, PolicyAgent, and ApprovalAgent use AI/ML API for reasoning and store provider/model metadata in the audit logs.

If `AIMLAPI_KEY` is missing or the AI/ML API call fails but `OPENROUTER_API_KEY` is set, the workflow automatically falls back to OpenRouter so the procurement demo still completes from start to finish.

If `FEATHERLESS_API_KEY` is set, FeatherlessReviewAgent runs a real open-source model review before human approval and stores provider/model metadata in the audit logs.

If a key is unavailable because coupons are exhausted, the app continues in degraded mode and clearly records that configuration is required. Do not claim live partner API usage unless the key is actually configured.
