# AC Agent — Associate Consultant AI
## MVP: ICU Family Briefing Engine + Clinical Note Generator

---

## Architecture

```
ac-agent/
├── backend/          FastAPI + PostgreSQL + Claude API
│   ├── main.py       App entry point
│   ├── models.py     SQLAlchemy ORM models
│   ├── schemas.py    Pydantic request/response schemas
│   ├── auth.py       JWT authentication
│   ├── config.py     Settings / environment
│   ├── database.py   Async DB engine
│   ├── routers/      API route handlers
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── briefings.py
│   │   └── notes.py
│   ├── services/     Business logic
│   │   ├── claude_service.py
│   │   ├── briefing_service.py
│   │   └── notes_service.py
│   └── prompts/      AI prompt library
│       ├── family_briefing.py
│       └── clinical_notes.py
│
├── frontend/         React Native (Expo)
│   └── src/
│       ├── screens/  All app screens
│       ├── components/ui.tsx  Shared components
│       ├── navigation/
│       ├── context/  Auth + Patient state
│       ├── services/api.ts  Backend client
│       ├── hooks/
│       └── utils/design.ts  Design tokens
│
└── docker-compose.yml
```

---

## Sprint 1 Setup — Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Desktop
- Expo Go app on iPhone/Android for testing

### 1. Clone and configure

```bash
git clone https://github.com/emcdigitals/ac-agent.git
cd ac-agent
cp backend/.env.example backend/.env
# Edit backend/.env — add ANTHROPIC_API_KEY
```

### 2. Start database

```bash
docker-compose up db -d
```

### 3. Start backend

```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

The local seed defaults to `doctor@example.com` / `ChangeMe123!`. Override these
with `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`, and never use the defaults in
a shared environment.

### 4. Start frontend

```bash
cd frontend
npm install
npx expo start
```

Scan QR code with Expo Go on your phone.

For a physical phone, set `EXPO_PUBLIC_API_URL` to the backend's reachable LAN or
HTTPS address; `localhost` points to the phone itself.

---

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/login | Obtain JWT token |
| GET  | /patients | Active patient list |
| POST | /patients | Add patient |
| PATCH| /patients/{id}/consent | Record AI consent |
| POST | /briefings/generate | Generate family briefing |
| POST | /briefings/complete | File briefing log |
| POST | /notes/generate | Generate SOAP note |
| POST | /notes/approve | Approve and file note |
| POST | /notes/discharge/{id} | Generate discharge summary |

---

## Clinical Data Flow

```
Associate confirms patient data
    ↓
POST /briefings/generate (payload: vitals, labs, ventilator, specialists)
    ↓
Backend builds 3-layer prompt (system + specialty supplement + patient data)
    ↓
Claude generates structured JSON briefing document
    ↓
App receives BriefingDocument → displays on BriefingPreview screen
    ↓
Associate reviews → taps "Start Live Briefing" → BriefingCopilot screen
    ↓
Live meeting: checklist + Q&A + milestones + do-not-say
    ↓
Meeting ends → BriefingComplete screen → file formal log
    ↓
POST /briefings/complete → permanent patient record entry
```

---

## HITL (Human-in-the-Loop) Design

Every AI output goes through this approval flow:

1. **Generate** — Claude produces draft (stored as `status: draft`)
2. **Review** — Associate reads section by section (scroll enforcement)  
3. **Edit** — Inline editing with full audit trail of changes
4. **Approve** — Single tap approval with timestamp + clinician credentials
5. **File** — Immutable record created (addendum-only policy)

No AI content reaches the patient record without explicit Associate approval.

---

## Privacy and compliance readiness

- **DPDPA 2023 workflow** — Consent is recorded per patient before AI processing
- **Data processing** — Clinical prompt content is sent to the configured AI provider; deployers must execute the appropriate data-processing agreements and verify residency requirements
- **Infrastructure** — PostgreSQL and application hosting must be configured for the hospital's approved region and retention policy
- **Medico-Legal** — All notes carry approving clinician name, designation, registration number, timestamp
- **Audit Trail** — Every AI call, every edit, every approval logged
- **AI Transparency** — All generated notes marked "Generated with AI assistance"

These controls support compliance implementation but do not, by themselves,
certify the deployment as DPDPA-, NMC-, or hospital-policy-compliant. Complete a
privacy, security, clinical-safety, and medico-legal review before real patient use.

---

## Verification

```bash
cd frontend
npm install
npx tsc --noEmit
npx expo export --platform web

cd ../backend
python -m compileall -q .
python -c "import main; print(main.app.title)"
```

---

## Phase 2 Roadmap

- ABDM / FHIR EHR integration
- Live call co-pilot with real-time transcription (Deepgram)
- WhatsApp referral messaging (Meta Business API)
- Urgency scoring engine
- Order management + nursing compliance tracking
- All 12 specialty modules
- Hindi + regional language support

---

## Team

- **CTO / Lead**: Architecture, backend, Claude integration
- **Frontend Dev**: React Native mobile app
- **AI Engineer**: Prompt design, output validation, safety guardrails
- **Domain Expert**: Dr. Shivesh Kumar, Cardiologist — EasyMyCare / EMC Digitals

---

*EMC Digitals — Healthcare AI Platform*  
*AWS Mumbai | DPDPA Compliant | NMC Aligned*
