# 🏆 ProcureFlow AI — Intelligent Procurement Orchestrator

[![Band](https://img.shields.io/badge/Powered%20by-Band-6C47F5)](https://bandprotocol.com)
[![AI/ML API](https://img.shields.io/badge/AI-OpenRouter-FF6B35)](https://openrouter.ai)
[![LangChain](https://img.shields.io/badge/LangChain-v0.2-1C3C3C)](https://langchain.com)
[![CrewAI](https://img.shields.io/badge/CrewAI-v0.30-FFD700)](https://crewai.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.111-009688)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Supabase-v2-3ECF8E)](https://supabase.com)

> **Track:** Track 1 (Internal Enterprise Workflows) — Band of Agents Hackathon 2026

A multi-agent procurement and vendor approval system where specialized AI agents collaborate through **Band** to fully automate enterprise purchase requests — from vendor discovery and risk scoring to policy compliance and human sign-off.

## ✨ Why This Wins

Procurement is a universal enterprise pain point. It's multi-step, involves multiple stakeholders, and is a perfect showcase for:
- **Agent-to-agent handoffs** via Band rooms
- **Human-in-the-loop design** with clear approval workflows
- **Audit-trail generation** with tamper-evident SHA-256 seals
- **Cross-framework orchestration** (LangChain + CrewAI + Custom Python)

## 🤖 The 4 Agents

| Agent | Role | Framework |
|---|---|---|
| `@Intake` | Parses purchase request (vendor, amount, category, justification) | LangChain |
| `@RiskAgent` | Scores vendor risk using AI/ML API (news, financials, compliance flags) | Custom Python + OpenRouter |
| `@PolicyAgent` | Checks request against company procurement policy rules | CrewAI |
| `@ApprovalAgent` | Summarizes findings, requests human sign-off, generates audit packet | LangChain |

All 4 communicate context exclusively through **Band rooms** — the core collaboration layer.

## 🔄 Agent Workflow

```
User submits purchase request (vendor, amount, purpose)
        ↓
@Intake parses & posts structured context to Band room
        ↓
@RiskAgent picks up from Band, scores vendor via AI/ML API, posts risk report
        ↓
@PolicyAgent reads risk + request from Band, checks policy rules, posts verdict
        ↓
@ApprovalAgent reads all context from Band, writes human-readable decision memo
        ↓
Human approves or rejects via UI → SHA-256 audit packet generated & sealed
```

## 🛠️ Tech Stack

- **Band SDK** — Agent-to-agent communication via shared rooms
- **OpenRouter (AI/ML API)** — Powers risk analysis, policy checks, and summary generation
- **LangChain** — `@Intake` + `@ApprovalAgent` orchestration
- **CrewAI** — `@PolicyAgent` role definition and task execution
- **Python 3.11 / FastAPI** — Backend API with async agent runners
- **Next.js 14 (App Router)** — Frontend dashboard with real-time agent timeline
- **Supabase** — PostgreSQL for request history, agent logs, and decisions
- **Vercel** — Frontend deployment
- **Railway** — Backend deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project
- Band account (use code `BANDHACK26` for Pro)
- OpenRouter API key

### 1. Clone & Setup

```bash
git clone https://github.com/FaisalBasit/ProcureFlow-AI.git
cd ProcureFlow-AI/procureflow-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual API keys:
# - BAND_API_KEY, BAND_ROOM_ID, BAND_WEBHOOK_SECRET
# - OPENROUTER_API_KEY
# - SUPABASE_URL, SUPABASE_KEY
```

### 3. Database Setup

Run the migration in your Supabase SQL editor:
- `supabase/migrations/001_init.sql`

### 4. Run Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Use the API

```bash
# Submit a purchase request
curl -X POST http://localhost:8000/api/procurement/submit-and-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_name": "Acme Cloud Services",
    "amount": 15000,
    "category": "software",
    "justification": "Annual SaaS subscription for cloud infrastructure monitoring"
  }'

# Approve the request
curl -X POST http://localhost:8000/api/procurement/approve \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "<request_id_from_submit>",
    "approved": true,
    "signed_by": "John Manager"
  }'
```

## 📁 Project Structure

```
procureflow-ai/
├── agents/
│   ├── intake_agent.py          # @Intake — LangChain
│   ├── risk_agent.py            # @RiskAgent — Custom Python + OpenRouter
│   ├── policy_agent.py          # @PolicyAgent — CrewAI
│   └── approval_agent.py        # @ApprovalAgent — LangChain
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── routes/
│   │   ├── procurement.py       # POST /submit, GET /requests, POST /approve
│   │   └── webhook.py           # Band webhook receiver
│   ├── services/
│   │   ├── band_client.py       # Band SDK wrapper
│   │   ├── aiml_client.py       # OpenRouter AI client
│   │   └── audit.py             # SHA-256 audit packet generator
│   └── db/
│       └── supabase_client.py   # Supabase CRUD operations
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Request submission form
│   │   ├── dashboard/page.tsx   # Live audit trail
│   │   └── approve/page.tsx     # Human approval UI
│   └── components/
│       ├── RequestForm.tsx
│       ├── AgentTimeline.tsx
│       └── AuditPacket.tsx
├── supabase/migrations/
│   └── 001_init.sql             # Database schema
├── .env.example
├── requirements.txt
└── README.md
```

## 🏅 Key Differentiators

1. **Cross-framework agents** — LangChain + CrewAI + custom Python in one Band room
2. **Veto mechanic** — `@PolicyAgent` can block and force re-evaluation before human sees it
3. **SHA-256 audit trail** — Every decision is sealed with a tamper-evident hash
4. **Human-in-the-loop** — Approval requires explicit human action via the UI
5. **Real enterprise use case** — Every procurement team can relate immediately

## 📝 API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/procurement/submit` | Submit a purchase request |
| POST | `/api/procurement/submit-and-process` | Submit + run full agent pipeline |
| GET | `/api/procurement/requests` | List all requests |
| GET | `/api/procurement/requests/{id}` | Get request details + logs |
| GET | `/api/procurement/requests/{id}/status` | Get current status |
| GET | `/api/procurement/requests/{id}/audit` | Get audit packet |
| POST | `/api/procurement/approve` | Submit human decision |
| POST | `/api/webhook/band` | Band webhook receiver |
| GET | `/health` | Health check |

## 📄 License

MIT — See [LICENSE](LICENSE) for details.

---

*Built for the [Band of Agents Hackathon](https://lablab.ai) — June 2026*