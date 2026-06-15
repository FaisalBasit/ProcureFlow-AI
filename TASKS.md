# ProcureFlow AI — Cline Task List
> Give Cline ONE task at a time. Test and confirm it works before moving to the next.
> Each task has a clear goal, expected output, and test to verify before proceeding.

---

## TASK-01 — Project Scaffold

**Goal:** Create the full folder structure and base config files.

**Instructions for Cline:**
```
Create the following folder structure under D:\lablab.ai\procureflow-ai\:

agents/
backend/
  routes/
  services/
  db/
frontend/
  app/
    dashboard/
    approve/
  components/
supabase/
  migrations/

Also create these files:
- requirements.txt with: fastapi, uvicorn, python-dotenv, langchain, langchain-openai, crewai, httpx, supabase
- .env.example with placeholders:
    BAND_API_KEY=
    AIML_API_KEY=
    SUPABASE_URL=
    SUPABASE_KEY=
    BAND_ROOM_ID=
- README.md with project title and one-line description
```

**✅ Test before proceeding:**
- [ ] All folders exist
- [ ] requirements.txt, .env.example, README.md are created
- [ ] Copy .env.example to .env and fill in your real keys

---

## TASK-02 — Band SDK Setup & Connection Test

**Goal:** Connect to Band, create a room, and send a test message via the Band Agent API.

**Instructions for Cline:**
```
Create backend/services/band_client.py

It should:
1. Load BAND_API_KEY and BAND_ROOM_ID from .env
2. Have a function send_message(agent_name: str, content: dict) that posts a message to the Band room via the Band Agent API (HTTP POST)
3. Have a function get_messages() that fetches recent messages from the Band room

Then create a test script: backend/test_band_connection.py
- It should call send_message with agent_name="@Intake" and content={"test": "hello from ProcureFlow"}
- Print the response status and message ID
```

**✅ Test before proceeding:**
- [ ] Run `python backend/test_band_connection.py`
- [ ] Message appears in Band room on band.ai dashboard
- [ ] get_messages() returns the message you sent

---

## TASK-03 — @Intake Agent

**Goal:** Build the Intake agent that parses a procurement request and posts structured context to the Band room.

**Instructions for Cline:**
```
Create agents/intake_agent.py

Use LangChain with AI/ML API (OpenAI-compatible base URL: https://api.aimlapi.com/v1).

The agent should:
1. Accept input: { vendor: str, amount: float, purpose: str, category: str }
2. Use an LLM to extract and structure the request into a clean JSON summary
3. Post the structured summary to the Band room using band_client.send_message()
   with agent_name="@Intake"
4. Return the Band message ID

The structured output posted to Band should look like:
{
  "agent": "@Intake",
  "step": "intake_complete",
  "vendor": "...",
  "amount": ...,
  "purpose": "...",
  "category": "...",
  "summary": "LLM-generated one-paragraph summary of the request",
  "timestamp": "ISO timestamp"
}
```

**✅ Test before proceeding:**
- [ ] Run intake_agent.py directly with a test input (e.g. vendor="Acme Corp", amount=15000, purpose="Office laptops", category="IT Equipment")
- [ ] Structured JSON appears in Band room
- [ ] No errors, message ID returned

---

## TASK-04 — AI/ML API Client

**Goal:** Build a reusable wrapper for AI/ML API to be used by @RiskAgent.

**Instructions for Cline:**
```
Create backend/services/aiml_client.py

It should:
1. Load AIML_API_KEY from .env
2. Use the OpenAI-compatible endpoint: https://api.aimlapi.com/v1
3. Have a function analyze_vendor(vendor: str, amount: float, category: str) -> dict
   - Send a prompt asking the LLM to assess vendor risk based on vendor name, amount, and category
   - Ask it to return JSON with: { risk_score: int (1-10), risk_level: str, flags: list[str], reasoning: str }
   - Parse and return the JSON response
4. Handle errors gracefully — return a default risk object if the API call fails
```

**✅ Test before proceeding:**
- [ ] Run aiml_client.py directly with a test vendor
- [ ] Returns a valid dict with risk_score, risk_level, flags, reasoning
- [ ] Works without errors

---

## TASK-05 — @RiskAgent

**Goal:** Build the Risk agent that reads Intake's message from Band and posts a vendor risk report.

**Instructions for Cline:**
```
Create agents/risk_agent.py

It should:
1. Call band_client.get_messages() and find the latest message from "@Intake" with step="intake_complete"
2. Extract vendor, amount, category from that message
3. Call aiml_client.analyze_vendor() to get the risk assessment
4. Post the risk report to Band using band_client.send_message() with agent_name="@RiskAgent"

The message posted to Band should look like:
{
  "agent": "@RiskAgent",
  "step": "risk_complete",
  "vendor": "...",
  "risk_score": 7,
  "risk_level": "High",
  "flags": ["No public financials", "New vendor"],
  "reasoning": "...",
  "timestamp": "ISO timestamp"
}
```

**✅ Test before proceeding:**
- [ ] Run risk_agent.py after running intake_agent.py
- [ ] Risk report appears in Band room as a new message from @RiskAgent
- [ ] risk_score is a number 1-10, flags is a list

---

## TASK-06 — Policy Rules File

**Goal:** Define the procurement policy rules that @PolicyAgent will enforce.

**Instructions for Cline:**
```
Create backend/services/policy_rules.py

Define a list of 6 policy rules as Python dicts:
[
  { "id": "P01", "rule": "Purchases over $10,000 require manager approval", "threshold": 10000 },
  { "id": "P02", "rule": "High-risk vendors (score >= 7) require additional review", "threshold": 7 },
  { "id": "P03", "rule": "IT Equipment purchases must be in approved category list", "categories": ["IT Equipment", "Software", "Hardware"] },
  { "id": "P04", "rule": "New vendors with no track record require legal review" },
  { "id": "P05", "rule": "Single purchases must not exceed $50,000 without CFO sign-off", "threshold": 50000 },
  { "id": "P06", "rule": "All vendors must have a valid business registration" }
]

Also add a function check_policies(intake_data: dict, risk_data: dict) -> dict
that checks each rule against the provided data and returns:
{
  "passed": [...list of passed rule IDs...],
  "failed": [...list of failed rule IDs with reason...],
  "verdict": "APPROVED" | "FLAGGED" | "BLOCKED",
  "requires_escalation": bool
}
```

**✅ Test before proceeding:**
- [ ] Run policy_rules.py with test data (high amount + high risk score)
- [ ] Returns correct verdict: BLOCKED or FLAGGED for risky scenarios
- [ ] Returns APPROVED for low-risk, low-amount scenarios

---

## TASK-07 — @PolicyAgent

**Goal:** Build the Policy agent using CrewAI that reads Band context and posts a compliance verdict.

**Instructions for Cline:**
```
Create agents/policy_agent.py

Use CrewAI to define a Policy Compliance Officer agent.

It should:
1. Read Band messages and find the latest @Intake (step=intake_complete) and @RiskAgent (step=risk_complete) messages
2. Run policy_rules.check_policies() with the combined data
3. Use a CrewAI agent+task to write a short compliance memo based on the verdict
4. Post the verdict to Band with agent_name="@PolicyAgent"

The message posted to Band:
{
  "agent": "@PolicyAgent",
  "step": "policy_complete",
  "verdict": "FLAGGED",
  "failed_rules": ["P01", "P02"],
  "requires_escalation": true,
  "compliance_memo": "LLM-written paragraph explaining the compliance decision",
  "timestamp": "ISO timestamp"
}

IMPORTANT: If verdict is BLOCKED, set a "veto": true field. The @ApprovalAgent must respect this veto and not proceed to human approval without forced override.
```

**✅ Test before proceeding:**
- [ ] Run policy_agent.py after intake and risk agents have run
- [ ] Compliance verdict appears in Band room
- [ ] BLOCKED scenario correctly sets veto: true
- [ ] Compliance memo is readable and accurate

---

## TASK-08 — Audit Packet Generator

**Goal:** Build the SHA-256 audit trail generator.

**Instructions for Cline:**
```
Create backend/services/audit.py

It should have a function generate_audit_packet(band_messages: list, human_decision: str) -> dict
that:
1. Takes all Band room messages from this procurement request
2. Takes the human's final decision ("APPROVED" or "REJECTED")
3. Serializes everything to a canonical JSON string
4. Generates a SHA-256 hash of the full packet
5. Returns:
{
  "packet_id": "uuid4",
  "request_id": "...",
  "human_decision": "APPROVED",
  "agent_messages": [...all Band messages...],
  "timestamp": "ISO timestamp",
  "sha256_hash": "abc123..."
}
```

**✅ Test before proceeding:**
- [ ] Run audit.py with mock data
- [ ] Returns a dict with a valid sha256_hash (64 hex chars)
- [ ] Running the same data twice produces the same hash (deterministic)

---

## TASK-09 — @ApprovalAgent

**Goal:** Build the final agent that compiles all Band context into a human-readable decision memo.

**Instructions for Cline:**
```
Create agents/approval_agent.py

Use LangChain. It should:
1. Read all messages from Band room (Intake, Risk, Policy steps)
2. Check if PolicyAgent set veto: true → if so, post a BLOCKED notice to Band and stop
3. If not vetoed, use LLM to write a clean decision memo for the human approver summarizing:
   - What was requested
   - Vendor risk level and flags
   - Policy compliance result
   - Recommendation (Approve / Reject / Escalate)
4. Post to Band with agent_name="@ApprovalAgent":
{
  "agent": "@ApprovalAgent",
  "step": "awaiting_human_approval",
  "decision_memo": "...",
  "recommendation": "APPROVE" | "REJECT" | "ESCALATE",
  "request_id": "uuid"
}
5. Return the request_id so the frontend can poll for human decision
```

**✅ Test before proceeding:**
- [ ] Run approval_agent.py after all previous agents
- [ ] Decision memo appears in Band room
- [ ] Veto scenario: BLOCKED message posted, agent stops
- [ ] Memo is clear and readable

---

## TASK-10 — Full Orchestration Runner

**Goal:** Wire all 4 agents into a single pipeline runner.

**Instructions for Cline:**
```
Create backend/orchestrator.py

It should have a function run_procurement_workflow(request: dict) -> dict that:
1. Generates a request_id (uuid4)
2. Creates (or joins) a Band room for this request
3. Runs @Intake agent → waits for Band message confirmation
4. Runs @RiskAgent → waits for Band message confirmation
5. Runs @PolicyAgent → checks for veto
6. If veto: generate audit packet with decision=BLOCKED, return result
7. If no veto: runs @ApprovalAgent → returns request_id for human approval polling

Each step should have a 30-second timeout with error handling.
Log each step's start/end to console.
```

**✅ Test before proceeding:**
- [ ] Run orchestrator.py with a test request end-to-end
- [ ] All 4 agent messages appear in Band room in correct order
- [ ] Console shows step-by-step progress
- [ ] Returns a request_id at the end

---

## TASK-11 — Supabase Schema & Logging

**Goal:** Set up the database to store requests and agent decisions.

**Instructions for Cline:**
```
Create supabase/migrations/001_init.sql with these tables:

CREATE TABLE procurement_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor TEXT NOT NULL,
  amount DECIMAL NOT NULL,
  purpose TEXT,
  category TEXT,
  status TEXT DEFAULT 'PENDING',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id UUID REFERENCES procurement_requests(id),
  agent_name TEXT NOT NULL,
  step TEXT NOT NULL,
  payload JSONB,
  band_message_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id UUID REFERENCES procurement_requests(id),
  human_decision TEXT,
  audit_packet JSONB,
  sha256_hash TEXT,
  decided_at TIMESTAMPTZ DEFAULT NOW()
);

Then create backend/db/supabase_client.py with functions:
- save_request(request_data) -> request_id
- log_agent_step(request_id, agent_name, step, payload, band_message_id)
- save_decision(request_id, human_decision, audit_packet)
- get_request_with_logs(request_id) -> full request + all agent logs
```

**✅ Test before proceeding:**
- [ ] Run the SQL in Supabase dashboard — all 3 tables created
- [ ] Test supabase_client.py functions with mock data
- [ ] save_request returns a valid UUID
- [ ] get_request_with_logs returns complete data

---

## TASK-12 — FastAPI Backend

**Goal:** Expose the orchestration pipeline via REST API endpoints.

**Instructions for Cline:**
```
Create backend/main.py and backend/routes/procurement.py

Endpoints needed:

POST /api/submit-request
  Body: { vendor, amount, purpose, category }
  Action: saves to Supabase, runs orchestrator.run_procurement_workflow()
  Returns: { request_id, status, band_room_id }

GET /api/request/{request_id}
  Returns: full request data + all agent logs from Supabase

POST /api/decision/{request_id}
  Body: { decision: "APPROVED" | "REJECTED", approver_name: str }
  Action: generates audit packet, saves to Supabase, updates request status
  Returns: { audit_packet, sha256_hash }

GET /api/health
  Returns: { status: "ok" }

Enable CORS for all origins (for frontend dev).
Use async FastAPI with uvicorn.
```

**✅ Test before proceeding:**
- [ ] Run `uvicorn backend.main:app --reload`
- [ ] POST /api/submit-request triggers full agent pipeline
- [ ] GET /api/request/{id} returns agent logs
- [ ] POST /api/decision/{id} returns audit packet with SHA-256 hash
- [ ] Test all endpoints with curl or Postman

---

## TASK-13 — Next.js Frontend Setup + Request Form

**Goal:** Create the Next.js app with a procurement request submission form.

**Instructions for Cline:**
```
Inside D:\lablab.ai\procureflow-ai\frontend\ initialize a Next.js 14 app with TypeScript and Tailwind CSS.

Create app/page.tsx — the home page with a request submission form:
- Fields: Vendor Name, Amount ($), Purpose, Category (dropdown: IT Equipment, Software, Hardware, Office Supplies, Services, Other)
- Submit button: "Submit for Review"
- On submit: POST to http://localhost:8000/api/submit-request
- On success: redirect to /dashboard/{request_id}
- Show loading state while submitting
- Clean, professional UI using Tailwind
```

**✅ Test before proceeding:**
- [ ] `npm run dev` starts without errors
- [ ] Form renders correctly
- [ ] Submitting form calls the backend API
- [ ] Successful submission redirects to dashboard page (even if dashboard is empty for now)

---

## TASK-14 — Agent Timeline Dashboard

**Goal:** Build the dashboard that shows live agent progress for a request.

**Instructions for Cline:**
```
Create app/dashboard/[request_id]/page.tsx

It should:
1. On load, fetch GET /api/request/{request_id}
2. Poll every 3 seconds while status is PENDING
3. Display an AgentTimeline component showing each agent step as a card:
   - @Intake → @RiskAgent → @PolicyAgent → @ApprovalAgent
   - Each card shows: agent name, step status (pending/complete/blocked), key data from payload
   - Completed steps show in green, pending in grey, blocked in red
4. If latest step is "awaiting_human_approval", show the Approve/Reject buttons
5. If status is BLOCKED, show a red banner "Request Blocked by Policy Agent"

Create components/AgentTimeline.tsx for the timeline cards.
Use Tailwind for styling — keep it clean and professional.
```

**✅ Test before proceeding:**
- [ ] Dashboard loads and shows request data
- [ ] Agent cards appear as each agent completes
- [ ] Polling updates the UI without full page reload
- [ ] BLOCKED state shows red banner correctly

---

## TASK-15 — Human Approval UI + Audit Packet Display

**Goal:** Build the approve/reject flow and show the final audit packet.

**Instructions for Cline:**
```
In app/dashboard/[request_id]/page.tsx, when step is "awaiting_human_approval":
- Show the full decision_memo from @ApprovalAgent
- Show two buttons: ✅ Approve  ❌ Reject
- On click: POST to /api/decision/{request_id} with { decision, approver_name: "Human Reviewer" }
- After decision: show AuditPacket component

Create components/AuditPacket.tsx:
- Shows: Decision (APPROVED/REJECTED in big colored text), Timestamp, SHA-256 Hash (monospace font), link to download packet as JSON
- Should look like an official document / receipt

Keep it professional — this is the "wow moment" in the demo video.
```

**✅ Test before proceeding:**
- [ ] Approve button triggers API call and shows audit packet
- [ ] SHA-256 hash displays correctly
- [ ] Download JSON button works
- [ ] Full end-to-end flow works: Submit → Watch agents → Approve → See audit packet

---

## TASK-16 — Deployment

**Goal:** Deploy backend to Railway and frontend to Vercel.

**Instructions for Cline:**
```
Backend (Railway):
1. Create a Procfile: web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
2. Create railway.json with build config
3. Add all env vars to Railway dashboard
4. Update CORS in main.py to allow the Vercel frontend URL

Frontend (Vercel):
1. Create frontend/.env.local with: NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
2. Update all API calls in frontend to use NEXT_PUBLIC_API_URL
3. Deploy to Vercel via CLI or GitHub

After deployment:
- Test full flow on live URLs
- Note the live demo URL for hackathon submission
```

**✅ Test before proceeding:**
- [ ] Railway backend is live and /api/health returns ok
- [ ] Vercel frontend loads and can submit a request
- [ ] Full end-to-end flow works on production URLs
- [ ] Note both URLs for submission

---

## 🎬 FINAL TASKS (June 18–19)

### Demo Video (30–45 min effort)
- Record screen showing the full flow: form submission → 4 agents firing in Band room → dashboard updating live → human approval → audit packet
- Show the Band room on band.ai side by side with your frontend
- Keep it under 5 minutes, no fluff
- Upload to YouTube (unlisted) or Loom

### Slide Deck (1 hour effort)
Slides needed:
1. Title + tagline
2. The problem (enterprise procurement pain)
3. Solution overview (agent diagram)
4. How Band is the coordination layer (show the room)
5. Tech stack
6. Live demo screenshot
7. Business value + who would use this

### GitHub README
- Project description
- Architecture diagram (can be a simple text diagram)
- Setup instructions
- How to run locally
- Tech stack list

---

*Always test each task before moving to the next. If something fails, fix it before proceeding — compounding errors with Cline + DeepSeek are hard to untangle.*
