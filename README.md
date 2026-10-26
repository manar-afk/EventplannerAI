# EventPilot AI — Indian Event & Wedding Planning Assistant

EventPilot AI is a production-grade full-stack GenAI planning assistant designed specifically for weddings, birthdays, and community celebrations across India. It generates culturally grounded budgets in Indian Rupees (INR), milestone timelines (IST), vendor checklists, and personalized ideas.

---

## 🌟 Key Architecture & Engineering Highlights

1. **Deterministic Python Budget Engine (`backend/app/budget_engine.py`)**:
   - Pure functions with **integer rupee math only** (no floating point drift).
   - Strict separation of **Estimates vs. Actuals**.
   - Formula: `Remaining Budget = Total Budget - (Actual if entered, otherwise Estimate)`.
   - **AI Never Does Arithmetic**: Gemini suggests line items, unit costs, and basis weights. The backend engine computes allocations, totals, and flags over-budget scenarios without altering the user's budget.
   - **Guest-count scaling** recalculates **only** per-guest items (e.g. catering, return gifts); fixed costs (e.g. venue hall, floral mandap, DJ) remain untouched.

2. **IST Date & Timeline Engine (`backend/app/timeline_engine.py`)**:
   - Dates are evaluated strictly in `Asia/Kolkata` (IST) timezone.
   - Rejects past event dates at creation.
   - Computes backwards milestone offsets by event type. Overdue or imminent milestones are tagged with `is_overdue` / `is_at_risk` banners; dates are **never moved silently**.
   - Shows **days remaining**, not an artificial ticking timer.

3. **Gemini Integration & Transparent Provenance**:
   - Uses the unified `google-genai` SDK with structured JSON schemas and Pydantic validation.
   - Delimits user text inputs (`<USER_INPUTS>`) to guard against prompt injection.
   - Retries once on transient errors, enforces timeouts, and validates model output.
   - **Transparent Source Tagging**: Plans carry either `source: "gemini"` or `source: "rule-based-fallback"`. Fallback output is never labeled as AI.

4. **Security & Resiliency**:
   - Server-side request body size limit (1MB max).
   - Max length constraints on all input fields.
   - Generic client error responses with detailed server-side logging.
   - In-memory rate limiting based on `X-Forwarded-For` (Cloud Run proxy).
   - Zero `dangerouslySetInnerHTML`.

5. **Client Persistence with Schema Recovery**:
   - `LocalStoragePlanRepository` validates stored data with a Zod schema upon load.
   - If corrupted or malformed data is found in `localStorage`, it recovers gracefully without crashing and displays a helpful recovery notice.

---

## 🏗️ Tech Stack

- **Frontend**: React 18, TypeScript 5, Vite 5, Tailwind CSS, Vitest.
- **Backend**: Python 3.13, FastAPI, Pydantic v2, `google-genai` SDK, Uvicorn, Pytest.
- **Container**: Multi-stage `Dockerfile` (Node 22 compiles SPA, Python 3.13 serves API + SPA on `$PORT`).

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm (`npm.cmd` on Windows PowerShell)

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# (Optional) Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Backend endpoints:
- API Documentation: `http://localhost:8080/docs`
- Healthcheck: `http://localhost:8080/healthz`

### 3. Frontend Setup
```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server (proxies /api and /healthz to :8080)
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Running Tests

### Backend Tests (Pytest)
```bash
# Run all 17 Pytest unit and route tests
python -m pytest backend/tests -v
```
Covers:
- Integer rupee math and remaining balance calculations.
- Over-budget flagging when proposed estimates exceed the user's budget.
- Guest count scaling affecting only `per_guest` items.
- Past-date rejection (400 Bad Request).
- Overdue and at-risk milestone detection without altering computed dates.
- Gemini fallback on malformed JSON and schema mismatch.
- Static SPA serving from FastAPI.

### Frontend Tests (Vitest & TypeScript)
```bash
cd frontend

# Run 11 Vitest tests
npm test

# Run TypeScript type check
npm run lint

# Build production assets
npm run build
```
Covers:
- Indian currency formatting (`en-IN` lakh grouping, compact Lakh and Cr formats).
- Days remaining calculations and past event detection.
- `LocalStoragePlanRepository` schema validation, malformed JSON recovery, and state persistence.

---

## ☁️ Google Cloud Run Deployment

The project includes a single multi-stage `Dockerfile` where Stage 1 builds the Vite React application and Stage 2 serves both the compiled static assets and the FastAPI endpoints over `$PORT`.

### 1. Build and Deploy with Google Cloud SDK
```bash
# Set your Google Cloud Project
gcloud config set project YOUR_PROJECT_ID

# Build container image via Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/eventpilot-ai:latest .

# Deploy to Cloud Run
gcloud run deploy eventpilot-ai \
  --image gcr.io/YOUR_PROJECT_ID/eventpilot-ai:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,GEMINI_MODEL=gemini-2.5-flash \
  --memory 512Mi \
  --cpu 1
```

### 2. Secret Manager Integration for Production
In production, do not hardcode credentials in environment variables. Store your API Key in Google Cloud Secret Manager:
```bash
# 1. Create secret in Secret Manager
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic"
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=-

# 2. Grant Cloud Run service account access
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Deploy Cloud Run referencing the secret
gcloud run services update eventpilot-ai \
  --region us-central1 \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

> **Note on Vertex AI:** If your Cloud Run service account has `roles/aiplatform.user` granted, leave `GEMINI_API_KEY` empty. The `google-genai` SDK will automatically authenticate via Application Default Credentials (ADC).

---

## ⚙️ Environment Variables Reference

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | HTTP port listened to by Uvicorn (Cloud Run dynamic injection) | `8080` |
| `ENVIRONMENT` | Environment name (`development` / `production`) | `development` |
| `GEMINI_API_KEY` | Google AI Studio API key for local development | `""` |
| `GEMINI_MODEL` | Gemini model name (verify availability) | `gemini-2.5-flash` |
| `GEMINI_TIMEOUT_SECONDS` | Timeout for Gemini API calls | `18.0` |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:5173,...` |
| `MAX_BODY_BYTES` | Maximum incoming payload size in bytes | `1048576` (1MB) |
| `RATE_LIMIT_PER_MINUTE` | In-memory sliding window rate limit per client IP | `20` |

---

## 🔒 Security & Operational Considerations

- **Per-Instance Rate Limiting**: The rate limiter operates in-memory using a sliding window. In multi-instance Cloud Run environments, each instance maintains its own bucket evaluated against the client IP from the `X-Forwarded-For` header. For high-volume multi-region clustering, consider Google Cloud Armor or Redis.
- **LocalStorage Scope**: Event plans are persisted in client `localStorage` under `eventpilot_active_plan_v1`. Stored plans remain private to the user's browser/device.
- **Prompt Injection Defense**: User input fields (themes, styles, requirements) are strictly typed with max length limits and wrapped in `<USER_INPUTS>` delimiters within prompts to prevent system instruction overrides.

---

## 📝 Known Limitations

- **Browser Storage Quota**: Storing plans in `localStorage` is device-bound and will not synchronize across different devices or incognito sessions.
- **Offline Mode**: If offline and no prior plan was generated, new plans cannot be created without internet connectivity.
