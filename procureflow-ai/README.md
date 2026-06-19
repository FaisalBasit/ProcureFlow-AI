# ProcureFlow AI

ProcureFlow AI is a Band-coordinated procurement approval desk for enterprise purchase requests. Specialized agents review a request, exchange handoff events through a shared Band room, run AI/ML API reasoning plus Featherless open-source review, escalate to a human approver, and seal the final decision with a SHA-256 audit hash.

Track: Band of Agents Hackathon 2026, Internal Enterprise Workflows.

## Why It Matters

Procurement is slow because work moves across finance, security, policy, operations, and management. A simple purchase can get stuck in email threads, spreadsheet comments, and unclear ownership.

ProcureFlow AI turns that process into an auditable multi-agent workflow:

- Intake normalizes the request.
- Risk evaluates vendor and spend exposure.
- Policy checks procurement controls and can escalate or block.
- Featherless review adds an independent open-source model second opinion.
- Approval creates a human-readable decision memo.
- A human signs the decision.
- The system produces a tamper-evident audit packet.

## The Agents

| Agent | Responsibility | Band role |
| --- | --- | --- |
| IntakeAgent | Validates vendor, amount, category, and justification | Starts the shared room context |
| RiskAgent | Scores vendor/spend risk with AI/ML API reasoning | Posts risk report |
| PolicyAgent | Checks procurement rules and escalates or blocks | Posts compliance verdict |
| FeatherlessReviewAgent | Runs independent open-source model review through Featherless AI | Posts second-opinion review when configured |
| ApprovalAgent | Summarizes all findings and finalizes human decision | Posts approval memo and final decision |
| BandBridge | Records Band delivery success/failure in the audit log | Proves Band coordination status |

Each production demo should register the four required agents as External Agents in Band and place them in the same Band chat room. For the strongest partner-prize demo, add a fifth `ProcureFlow Featherless Review Agent`. See [docs/BAND_SETUP.md](docs/BAND_SETUP.md).

## End-To-End Flow

```text
Purchase request submitted
  -> IntakeAgent validates, posts purchase_request to Band, and @mentions RiskAgent
  -> RiskAgent analyzes, posts risk_report to Band, and @mentions PolicyAgent
  -> PolicyAgent checks controls, posts policy_verdict to Band
  -> FeatherlessReviewAgent runs open-source review through Featherless AI
  -> ApprovalAgent creates decision memo and posts approval_summary to Band
  -> Human approves/rejects in the UI
  -> ApprovalAgent posts final_decision to Band
  -> Supabase stores request, logs, decision, and SHA-256 audit hash
```

## What Judges Can Verify

1. Band Agents page contains the four required ProcureFlow External Agents, with optional Featherless review agent for partner-prize demos.
2. Band chat room contains the agents as participants.
3. A submitted request creates visible Band events and directed @mention handoffs from IntakeAgent, RiskAgent, PolicyAgent, Featherless review, and ApprovalAgent.
4. Dashboard status progresses beyond `pending` into `awaiting_approval` and then `approved` or `rejected`.
5. Approvals page shows AI/ML risk, policy verdict, Featherless review, approval summary, and human sign-off.
6. Audit Packet shows agent logs, BandBridge delivery records, decision, signer, and SHA-256 hash.

## Tech Stack

- Band Agent API for multi-agent coordination events.
- AI/ML API chat completions for risk, policy, and summary reasoning, with OpenRouter fallback for local resilience.
- Featherless AI open-source model inference for independent second-opinion review.
- FastAPI backend with isolated agent runners.
- Supabase/PostgreSQL for request history, agent logs, and decisions.
- Next.js 14 frontend for submit, dashboard, approval, and audit packet views.
- SHA-256 audit sealing for final decisions.

## Quick Start

### 1. Backend

```powershell
cd procureflow-ai
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

If the local venv is broken, `uv` also works:

```powershell
$env:UV_CACHE_DIR='D:\lablab.ai\.uv-cache'
$env:UV_PYTHON_INSTALL_DIR='D:\lablab.ai\.uv-python'
uv run --python 3.13 uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend

```powershell
cd procureflow-ai\frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### 3. Environment

Copy `.env.example` to `.env` and set:

```env
BAND_ROOM_ID=your_band_chat_room_id
BAND_INTAKE_API_KEY=your_intake_agent_key
BAND_RISK_API_KEY=your_risk_agent_key
BAND_POLICY_API_KEY=your_policy_agent_key
BAND_FEATHERLESS_REVIEW_API_KEY=optional_featherless_review_agent_key
BAND_APPROVAL_API_KEY=your_approval_agent_key

AI_PROVIDER=aimlapi
AIMLAPI_KEY=your_aimlapi_key
FEATHERLESS_API_KEY=your_featherless_key
OPENROUTER_API_KEY=optional_fallback_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Band setup details are in [docs/BAND_SETUP.md](docs/BAND_SETUP.md).
Final recording guidance is in [docs/FINAL_DEMO_CHECKLIST.md](docs/FINAL_DEMO_CHECKLIST.md).

### 4. Database

Run:

```sql
-- supabase/migrations/001_init.sql
```

in the Supabase SQL editor.

## Verification Commands

Check API health:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

Check Band readiness:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/procurement/band/status" -Method Get | ConvertTo-Json -Depth 8
```

Submit a request:

```powershell
$body = @{
  vendor_name='Acme Cloud Services'
  amount=15000
  category='software'
  justification='Annual cloud monitoring subscription for production deployment observability'
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/procurement/submit-and-process" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 10
```

Approve:

```powershell
$body = @{
  request_id='<request-id>'
  approved=$true
  signed_by='Jane Finance'
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/procurement/approve" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 10
```

## Demo Script

Use this order in the final video:

1. Problem: procurement approvals are fragmented and hard to audit.
2. Band setup: show four required ProcureFlow remote agents in Band, plus optional Featherless review agent if configured.
3. Chat room: show agents as participants.
4. Submit a realistic purchase request.
5. Show Band events appearing agent by agent, including policy handoff and open-source review.
6. Show Dashboard moving to `awaiting approval`.
7. Show Approvals page with AI/ML risk, policy, Featherless review, summary, and signer field.
8. Approve the request.
9. Show Audit Packet with SHA-256 hash and BandBridge records.
10. Close with business value: faster approvals, less manual coordination, better traceability.

## Judging Criteria Mapping

| Criterion | How ProcureFlow AI addresses it |
| --- | --- |
| Application of Technology | Specialized External Agents coordinate through Band Agent API events, directed handoffs, shared context, and task state in one room. |
| Presentation | UI exposes Submit, Dashboard, Approvals, Timeline, and Audit Packet views for a clean demo. |
| Business Value | Automates a real enterprise procurement workflow with human governance and traceability. |
| Originality | Combines Band handoffs, AI/ML API reasoning, Featherless open-source review, human approval, and SHA-256 audit sealing. |

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Backend health |
| GET | `/api/procurement/band/status` | Band credential and room readiness |
| POST | `/api/procurement/submit-and-process` | Submit request and run full agent pipeline |
| GET | `/api/procurement/requests` | List requests |
| GET | `/api/procurement/requests/{id}` | Request details with logs and decision |
| GET | `/api/procurement/requests/{id}/status` | Current status and agent actions |
| GET | `/api/procurement/requests/{id}/audit` | Final audit packet |
| POST | `/api/procurement/approve` | Human approval or rejection |
| POST | `/api/webhook/band` | Band webhook/event receiver |

## Repository Structure

```text
agents/                  Agent runners
backend/db/              Supabase persistence
backend/routes/          FastAPI API routes
backend/services/        Band, model-provider, Featherless, audit helpers
frontend/app/            Next.js pages
frontend/components/     UI components
supabase/migrations/     Database schema
docs/BAND_SETUP.md       Required Band setup checklist
docs/FINAL_DEMO_CHECKLIST.md Final submission recording checklist
```

## License

MIT
