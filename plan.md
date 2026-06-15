# 🏆 Band of Agents Hackathon — Winning Plan
> Deadline: June 19, 2026 · Prize Pool: $10,000+

---

## 🎯 Project Concept: **ProcureFlow AI** — Intelligent Procurement Orchestrator

A multi-agent procurement and vendor approval system where specialized AI agents collaborate through Band to fully automate enterprise purchase requests — from vendor discovery and risk scoring to policy compliance and human sign-off.

> **Why this wins:** Procurement is a universal enterprise pain point. It's multi-step, involves multiple stakeholders, and is a perfect showcase for agent-to-agent handoffs, human-in-the-loop design, and audit-trail generation — all things the judges care about.

> **Track:** Track 1 (Internal Enterprise Workflows) + eligibility for AI/ML API partner prize.

---

## 🤖 The 4 Agents (all collaborating via Band)

| Agent | Role | Framework |
|---|---|---|
| `@Intake` | Parses purchase request (vendor, amount, category, justification) | LangChain |
| `@RiskAgent` | Scores vendor risk using AI/ML API (news, financials, compliance flags) | Custom Python |
| `@PolicyAgent` | Checks request against company procurement policy rules | CrewAI |
| `@ApprovalAgent` | Summarizes findings, requests human sign-off, generates audit packet | LangChain |

All 4 communicate context exclusively through **Band rooms** — this is the core collaboration layer, not a wrapper.

---

## 🔄 Agent Workflow

```
User submits purchase request (vendor name, amount, purpose)
        ↓
@Intake parses & posts structured context to Band room
        ↓
@RiskAgent picks up from Band, scores vendor via AI/ML API, posts risk report back
        ↓
@PolicyAgent reads risk + request from Band, checks policy rules, posts compliance verdict
        ↓
@ApprovalAgent reads all context from Band, writes human-readable decision memo
        ↓
Human approves or rejects via Band → final SHA-256 audit packet generated
```

---

## 🛠️ Tech Stack

- **Band SDK** — agent-to-agent communication, shared rooms, context exchange
- **AI/ML API** — power `@RiskAgent` with model inference (reasoning, summarization)
- **LangChain** — `@Intake` + `@ApprovalAgent` orchestration
- **CrewAI** — `@PolicyAgent` role definition and task execution
- **Python 3.11 / FastAPI** — backend for agent runners + webhook endpoints
- **Next.js 14 (App Router)** — frontend dashboard to submit requests and view audit trail
- **Supabase** — store request history, audit logs, agent decisions
- **Vercel** — deploy frontend
- **Railway** — deploy FastAPI backend

---

## 📁 Project Folder Structure

```
D:\lablab.ai\procureflow-ai\
├── agents\
│   ├── intake_agent.py          # @Intake — LangChain
│   ├── risk_agent.py            # @RiskAgent — Custom Python + AI/ML API
│   ├── policy_agent.py          # @PolicyAgent — CrewAI
│   └── approval_agent.py        # @ApprovalAgent — LangChain
├── backend\
│   ├── main.py                  # FastAPI app entry point
│   ├── routes\
│   │   ├── procurement.py       # POST /submit-request
│   │   └── webhook.py           # Band webhook receiver
│   ├── services\
│   │   ├── band_client.py       # Band SDK wrapper
│   │   ├── aiml_client.py       # AI/ML API wrapper
│   │   └── audit.py             # SHA-256 audit packet generator
│   └── db\
│       └── supabase_client.py   # Supabase client
├── frontend\
│   ├── app\
│   │   ├── page.tsx             # Request submission form
│   │   ├── dashboard\
│   │   │   └── page.tsx         # Live audit trail view
│   │   └── approve\
│   │       └── page.tsx         # Human approval UI
│   └── components\
│       ├── RequestForm.tsx
│       ├── AgentTimeline.tsx    # Shows Band room messages live
│       └── AuditPacket.tsx
├── supabase\
│   └── migrations\
│       └── 001_init.sql         # Tables: requests, agent_logs, decisions
├── .env.example
├── requirements.txt
├── README.md
└── TASKS.md
```

---

## 📅 Day-by-Day Build Schedule

### Day 1 — Friday June 13
- [x] Enroll in hackathon on lablab.ai
- [ ] Create Band account, redeem `BANDHACK26` for Pro
- [ ] Read Band docs: agent API, rooms, context exchange, SDK setup
- [ ] Claim AI/ML API credits from lablab.ai dashboard
- [ ] Claim Featherless AI promo code `BOA26`
- [x] Set up project scaffold (folders, .env, requirements.txt)

### Day 2 — Saturday June 14
- [ ] Build + test `@Intake` agent
- [ ] Build + test `@RiskAgent`

### Day 3 — Sunday June 15
- [ ] Build + test `@PolicyAgent`
- [ ] Build + test `@ApprovalAgent`

### Day 4 — Monday June 16 (TODAY)
- [ ] Build Band SDK connection (TASK-02)
- [ ] Build + test `@Intake` agent (TASK-03)
- [ ] Build AI/ML API client → updated to OpenRouter (TASK-04)
- [ ] Build + test `@RiskAgent` (TASK-05)
- [ ] Build Policy Rules + `@PolicyAgent` (TASK-06 → TASK-07)
- [ ] Build Audit Packet + `@ApprovalAgent` (TASK-08 → TASK-09)
- [ ] Wire all 4 agents in full Band room flow (TASK-10)
- [ ] Build Supabase schema + logging (TASK-11)
- [ ] Build FastAPI backend (TASK-12)

### Day 5 — Tuesday June 17
- [ ] Build Next.js frontend (TASK-13 → TASK-14)
- [ ] Human approval UI + SHA-256 audit packet (TASK-15)

### Day 6 — Wednesday June 18
- [ ] Deploy backend to Railway, frontend to Vercel (TASK-16)
- [ ] End-to-end test with 3 realistic scenarios
- [ ] Record demo video (3–5 min showing live Band room)
- [ ] Write project description + prepare slide deck

### Day 7 — Thursday June 19
- [ ] Final review of all submission fields
- [ ] Submit on lablab.ai before **8:00 PM PKT**
- [ ] Tag AI/ML API usage clearly for partner prize

---

## 📋 Submission Checklist

- [ ] Project Title: **ProcureFlow AI**
- [ ] Short Description (2–3 sentences)
- [ ] Long Description (problem, agent roles, Band usage, business value)
- [ ] Cover image (1280×720)
- [ ] Video presentation (3–5 min live demo)
- [ ] Slide deck (PDF or link)
- [ ] Public GitHub repo with README
- [ ] Live demo URL (Vercel frontend)
- [ ] Tech tags: Band, LangChain, CrewAI, AI/ML API, Python, Next.js, Supabase

---

## 🏅 Judging Criteria Alignment

| Criterion | How the project scores |
|---|---|
| **Application of Technology** | Band is the actual coordination layer — all 4 agents communicate exclusively via Band rooms with structured context, task handoffs, and shared state |
| **Presentation** | Clear agent diagram, live Band room visible in demo, simple UI makes the workflow easy to follow |
| **Business Value** | Procurement automation is a real enterprise pain point — reduces manual coordination, speeds approvals, provides audit readiness |
| **Originality** | Multi-framework (LangChain + CrewAI + custom) agents in one Band room; PolicyAgent veto mechanic; tamper-evident audit trail |

---

## 💡 Differentiators

1. **Cross-framework agents** — LangChain + CrewAI + custom Python all in one Band room
2. **Veto mechanic** — `@PolicyAgent` can block and force re-evaluation before human sees it
3. **Audit trail** — every Band message logged and sealed with SHA-256 on final decision
4. **Human-in-the-loop** — approval is human-triggered via UI, posting back into Band
5. **Real use case** — every enterprise has procurement; judges immediately relate

---

## ⚠️ Important Reminders

- Cancel Band Pro before next billing cycle if not continuing
- Cancel AI/ML API and Featherless trials if not needed after the event
- All code must be original and MIT-licensed
- Prize distribution can take up to 90 days

---

*Last updated: June 15, 2026*
