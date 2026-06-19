# Submission Copy

## Project Title

ProcureFlow AI: Band-Coordinated Procurement Approval Desk

## Short Description

Four specialized Band agents review enterprise purchase requests, exchange handoffs in a shared Band room, escalate to a human approver, and seal the final decision with a SHA-256 audit packet.

## Long Description

ProcureFlow AI solves a common enterprise workflow problem: purchase approvals are slow, fragmented, and hard to audit. A single request often moves across finance, vendor risk, policy review, and management sign-off with no clear shared state.

ProcureFlow AI turns that process into a coordinated multi-agent workflow on Band. IntakeAgent parses and normalizes the purchase request. RiskAgent evaluates vendor and spend exposure using AI reasoning. PolicyAgent checks procurement controls and can flag or block the request. ApprovalAgent gathers all context into a human-readable decision memo and waits for explicit human sign-off. Each agent posts its handoff/result into the same Band chat room using its own External Agent API key, so judges can inspect the coordination live.

After the human decision, the system writes an audit packet containing the original request, risk report, policy verdict, approval summary, signer, timestamp, and SHA-256 hash. The frontend provides a complete enterprise workflow: Submit, Dashboard, Approvals, Agent Timeline, and Audit Packet.

The result is a practical internal enterprise workflow where Band is the visible coordination layer, humans remain in control, and every decision is traceable.

## Suggested Tags

Band Agent API, Band Agentic Mesh, AI/ML API, OpenRouter, FastAPI, Next.js, Supabase, Procurement, Compliance, Human-in-the-loop, Audit Trail

## Video Outline

1. Show the pain: procurement approvals lack shared state and auditability.
2. Show Band Agents page with four ProcureFlow external agents.
3. Show Band chat room with all four agents as participants.
4. Submit a realistic purchase request.
5. Show Band events appearing from IntakeAgent, RiskAgent, PolicyAgent, and ApprovalAgent.
6. Show Dashboard status changing to `awaiting approval`.
7. Show Approvals page with risk, policy, summary, and human signer.
8. Approve the request.
9. Show final Audit Packet and SHA-256 hash.
10. End on business value: faster approvals, clearer accountability, audit-ready governance.

## One-Sentence Pitch

ProcureFlow AI is a procurement war room where Band agents coordinate risk, policy, and approval work in real time, then hand a human an audit-ready decision packet.
