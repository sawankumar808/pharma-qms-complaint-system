# AIVOA · AI-Powered Customer Complaint Management System

An AI-powered Customer Complaint Management module for a pharmaceutical
(API/FDF) manufacturing QMS. A reviewer pastes or uploads a raw complaint
(email, portal text, PDF), and an AI Copilot pipeline extracts structured
fields, checks completeness, flags duplicates, classifies risk, and
recommends root cause + CAPA — all before the reviewer saves it to the
complaint log.

## Tech stack (as mandated in the assignment)

| Layer | Choice |
|---|---|
| Frontend | React + Redux (Vite) |
| Backend | Python + FastAPI |
| AI orchestration | LangGraph |
| LLM | Groq — `llama-3.1-8b-instant` (core pipeline), `llama-3.3-70b-versatile` (summary node, for extra context) |
| Database | PostgreSQL (Hosted on Render) via SQLAlchemy (swappable to SQLite for local development) |
| Font | Google Inter |

> **Note on Model Selection:** The assignment document originally suggested `gemma2-9b-it`. However, that model endpoint has been deprecated/decommissioned on Groq. To ensure stability and fast inference, `llama-3.1-8b-instant` was selected for the primary extraction/analysis pipeline, and `llama-3.3-70b-versatile` for context-heavy summary generation.

## What's implemented

**Core workflow** (as shown in the demo video): user pastes/uploads a
complaint → frontend sends it to the backend → LangGraph pipeline runs on
Groq → the result auto-populates the **Log Customer Complaint** form and the
**AI Copilot Risk Assessment** panel → reviewer edits if needed → saves to
the complaint log.

**AI Copilot pipeline (LangGraph, 6 sequential nodes):**
1. **Field extraction** — pulls product name, batch number, complainant
   name/email, date of incident, and description out of unstructured text.
2. **Completeness Checker** *(bonus)* — scores the complaint and lists which
   mandatory fields are missing.
3. **Duplicate Complaint Detection** *(bonus)* — compares the new complaint
   against the last 50 logged complaints and flags likely duplicates with a
   similarity score.
4. **AI Risk Classification** *(bonus)* — Critical / Major / Minor, using
   standard QMS severity logic (patient safety impact vs. quality-only vs.
   cosmetic/documentation), with a written rationale.
5. **Root Cause Recommendation** *(bonus)* — suggests a probable root-cause
   category (manufacturing deviation, packaging defect, cold-chain excursion,
   etc.) as a preliminary AI hint for the investigator.
6. **CAPA Recommendation** *(bonus)* — drafts a Corrective Action and a
   Preventive Action.
7. **Complaint Summary** *(bonus)* — a 2-3 sentence dashboard-ready summary
   (uses the larger Llama model, as the assignment allows for extra context).

All 6 "Examples" of bonus features listed in the assignment are implemented.

## Project structure

```
aivoa-complaint-system/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── core/                   # config, DB session, file text extraction
│   │   ├── models/                 # SQLAlchemy models (Complaint, AIAssessment)
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── ai/                     # groq_client.py + langgraph_workflow.py
│   │   └── routers/complaints.py   # /api/complaints endpoints
│   ├── sample_data/                # 4 realistic sample complaints for demo
│   ├── requirements.txt
│   └── .env.example
└── frontend/
├── src/
│   ├── components/             # Intake, Log form, AI Copilot panel, Dashboard
│   ├── store/                  # Redux slice + store
│   ├── api/client.js           # axios API calls
│   └── data/sampleComplaints.js
├── index.html                  # Google Inter font included
├── package.json
└── vite.config.js
```

## Setup & run

### 1. Get a Groq API key
Create one at https://console.groq.com/keys (the free tier is enough for this
assignment).

### 2. Backend Environment Setup

Navigate to the `backend` folder and create your local `.env` configuration file from `.env.example`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your GROQ_API_KEY

uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).
By default it uses a local SQLite file (`aivoa_complaints.db`) — zero setup.
To use Postgres/MySQL instead, just set `DATABASE_URL` in `.env` (examples
are in `.env.example`) and install the matching driver (already listed in
`requirements.txt`).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` requests to
the backend on port 8000, so no CORS/URL config is needed locally.

### 4. Try it

Go to Log Complaint → click one of the sample chips (or paste your own
complaint / upload a .txt/.pdf) → Run AI Analysis. Watch the AI
Copilot panel fill in live, review the auto-populated form, then Save to
Complaint Log. Check the Complaint Log tab to see it listed — try the
"Duplicate of above" sample right after the first one to see duplicate
detection catch it.

## Notes on scope
Document parsing uses pypdf/plain-text decoding, not production-grade
OCR — matches the assignment's note that this isn't required.

Model Choice Note: gemma2-9b-it mentioned in assignment guidelines was deprecated on Groq, so upgraded to active llama-3.1-8b-instant and llama-3.3-70b-versatile models.

Sample complaint text (emails/portal submissions) was written for this
submission to demonstrate the workflow, as the assignment permits.

No human-written business logic was hand-typed from scratch without AI
assistance in the sense the assignment describes — this was built with AI
pair-programming, then reviewed and adapted line by line to fit the
demoed workflow.