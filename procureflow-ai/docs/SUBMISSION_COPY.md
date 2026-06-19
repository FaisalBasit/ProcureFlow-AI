# Submission Copy

## Project Title

ProcureFlow AI: Band-Coordinated Procurement Approval Desk

## Short Description

Band-connected procurement agents review enterprise purchase requests, exchange handoffs in a shared Band room, use AI/ML API plus Featherless AI for decision support, escalate to a human approver, and seal the final decision with a SHA-256 audit packet.

## Long Description

ProcureFlow AI solves a common enterprise workflow problem: purchase approvals are slow, fragmented, and hard to audit. A single request often moves across finance, vendor risk, policy review, and management sign-off with no clear shared state.

ProcureFlow AI turns that process into a coordinated multi-agent workflow on Band. IntakeAgent parses and normalizes the purchase request. RiskAgent evaluates vendor and spend exposure using AI/ML API-compatible reasoning. PolicyAgent checks procurement controls and can flag or block the request. FeatherlessReviewAgent runs an independent open-source model review through Featherless AI before final approval. ApprovalAgent gathers all context into a human-readable decision memo and waits for explicit human sign-off. Each agent posts its handoff/result into the same Band chat room using External Agent API keys, so judges can inspect the coordination live.

After the human decision, the system writes an audit packet containing the original request, AI/ML risk report, policy verdict, Featherless review, approval summary, signer, timestamp, and SHA-256 hash. The frontend provides a complete enterprise workflow: Submit, Dashboard, Approvals, Agent Timeline, and Audit Packet.

The result is a practical internal enterprise workflow where Band is the visible coordination layer, humans remain in control, and every decision is traceable.

## Suggested Tags

Band Agent API, Band Agentic Mesh, AI/ML API, Featherless AI, FastAPI, Next.js, Supabase, Procurement, Compliance, Human-in-the-loop, Audit Trail

## Video Outline

1. Show the pain: procurement approvals lack shared state and auditability.
2. Show Band Agents page with the four required ProcureFlow external agents; show the optional Featherless review agent if configured.
3. Show Band chat room with agents as participants.
4. Submit a realistic purchase request.
5. Show Band events appearing from IntakeAgent, RiskAgent, PolicyAgent, Featherless review, and ApprovalAgent.
6. Show Dashboard status changing to `awaiting approval`.
7. Show Approvals page with AI/ML risk, policy, Featherless review, summary, and human signer.
8. Approve the request.
9. Show final Audit Packet and SHA-256 hash.
10. End on business value: faster approvals, clearer accountability, audit-ready governance.

## One-Sentence Pitch

ProcureFlow AI is a procurement war room where Band agents coordinate risk, policy, and approval work in real time, then hand a human an audit-ready decision packet.

## Judging Criteria Mapping

Application of Technology: Band is the collaboration layer inside the workflow. Agents post structured task/result events, hand off work with directed mentions, share request state, and leave BandBridge delivery evidence in the audit log.

Presentation: The demo has a clear path: Submit, live Agent Timeline, Band room transcript, Dashboard, Approvals, and final Audit Packet. The UI exposes the role of each agent and the model/provider evidence.

Business Value: ProcureFlow automates a real internal enterprise approval process where procurement, risk, compliance, and management usually coordinate manually across email and spreadsheets.

Originality: The system combines Band handoffs, AI/ML API reasoning, Featherless open-source second review, human-in-the-loop governance, and SHA-256 audit sealing instead of being a single chatbot or linear form automation.
