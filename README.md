# EventPilot AI — Indian Event & Wedding Planning Assistant

EventPilot AI is a full-stack GenAI planning assistant designed specifically for weddings, birthdays, and community celebrations across India. It generates culturally grounded budgets in Indian Rupees (INR), milestone schedules (IST), vendor checklists, and personalized ideas.

---

## 🌟 Key Architecture & Engineering Standards

1. **Deterministic Python Budget Engine (`backend/app/budget_engine.py`)**:
   - Pure functions with **strict integer rupee math only** (no floating-point drift).
   - Strict separation of **Estimates vs. Actuals**.
   - Formula: `Remaining Budget = Total Budget - Total Effective (Actual where entered, otherwise Estimate)`.
   - `is_over_budget = remaining_budget < 0` and `over_budget_amount = max(0, -remaining_budget)`.
   - **AI Never Does Arithmetic**: Gemini suggests line items, unit costs, and basis weights. The backend engine computes allocations, totals, and flags over-budget scenarios without altering the user's budget.
   - **Guest-count scaling** uses integer half-up math: `(2 * amount * new + old) // (2 * old)`. Recalculates **only** per-guest items (e.g. catering, favors); fixed costs remain untouched. User-entered actuals are never modified and are flagged for review.

2. **IST Date & Timeline Engine (`backend/app/timeline_engine.py`)**:
   - Evaluated strictly in `Asia/Kolkata` (IST) timezone.
   - Rejects past event dates at creation (400 Bad Request).
   - Computes backwards milestone offsets by event type. Overdue and at-risk flags apply strictly to **incomplete** milestones; computed dates are **never moved silently**.
   - Shows **days remaining**, not a ticking timer.

3. **Gemini Integration & Transparent Provenance**:
   - Uses the unified `google-genai` SDK with Vertex AI Application Default Credentials (ADC) as default.
   - User inputs inside `<USER_INPUTS>` are HTML-escaped and treated strictly as untrusted data.
   - Retries only transient errors (429, 5xx, timeouts) and enforces `HttpOptions` timeouts.
   - **Transparent Source Tagging**: Every plan carries either `source: "gemini"` or `source: "rule-based-fallback"`. Fallback output displays: *"Template plan, not personalised."*

4. **Security & Resiliency**:
   - Path-traversal safe static file serving (`candidate.is_relative_to(DIST)`).
   - Fail-closed CORS: empty `CORS_ORIGINS` defaults to localhost in development and `[]` in production; wildcard `*` is forbidden in production.
   - Thread-safe sliding-window rate limiter evaluating client IP from the right of `X-Forwarded-For` (`parts[-trusted_proxy_hops]`) with a 10,000-key memory cap and global cap.
   - Zero `dangerouslySetInnerHTML`.

---

## 🏗️ Tech Stack

- **Frontend**: React 18, TypeScript 5, Vite 5, Tailwind CSS, Vitest.
- **Backend**: Python 3.13, FastAPI, Pydantic v2, `google-genai` SDK, Uvicorn, Pytest.
- **Container**: Multi-stage `Dockerfile` (Node 22 compiles SPA, Python 3.13 serves API + SPA on `$PORT` as non-root `appuser`).

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.13
- Node.js 18+ and npm (`npm.cmd` on Windows PowerShell)

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# (Optional) Authenticate with Google Cloud Vertex AI ADC for local development:
gcloud auth application-default login

# Start backend server
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Endpoints:
- API Documentation: `http://localhost:8080/docs`
- Healthcheck: `http://localhost:8080/healthz` (returns `{"status":"ok"}`)

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

## 🧪 Running Tests & End-to-End Verification

### Backend Tests (Pytest)
```bash
# Run all 37 Pytest tests
python -m pytest backend/tests -v
```

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

### End-to-End Journey Verification
```bash
# Run the automated end-to-end integration verification script
python verify_e2e.py
```

---

## ☁️ Google Cloud Run Deployment

Deployment uses Google Cloud Run with Vertex AI Application Default Credentials (no API keys or Secret Manager needed).

### 1. Vertex AI GCP Project Setup
Ensure the following are configured on your Google Cloud Project:
1. **Enable Vertex AI API**:
   ```bash
   gcloud services enable aiplatform.googleapis.com run.googleapis.com
   ```
2. **Billing Enabled**: Confirm Cloud Billing is active on your project.
3. **Grant Vertex AI User Role to Cloud Run Runtime Service Account**:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

### 2. Deploy to Cloud Run
Deploy directly from source using Google Cloud Build:
```bash
gcloud run deploy eventpilot-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --max-instances 3 \
  --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash
```

### 3. Reading Cloud Run Logs for Diagnostics
If Gemini calls encounter issues in production, view detailed diagnostic logs:
```bash
gcloud run services logs read eventpilot-ai --limit 50
```
Common diagnostic hints logged server-side:
- **Status 403**: Service account lacks `roles/aiplatform.user`.
- **Status 404**: Gemini model not available in the configured region.
- **"API has not been used"**: `aiplatform.googleapis.com` is not enabled on the project.

---

## ⚙️ Environment Variables Reference

| Variable | Description | Default | Allowed / Range |
| :--- | :--- | :--- | :--- |
| `PORT` | HTTP port listened to by Uvicorn | `8080` | `1 – 65535` |
| `ENVIRONMENT` | Environment name | `development` | `development`, `production` |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID for Vertex AI ADC | None | String |
| `GOOGLE_CLOUD_LOCATION` | GCP Region for Vertex AI | `us-central1` | String |
| `GEMINI_API_KEY` | Optional local development API key | `""` | Secret string |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` | String |
| `GEMINI_TIMEOUT_SECONDS`| HttpOptions timeout for model calls | `20.0` | `0.0 – 60.0` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated; `*` forbidden in production) | `""` | String |
| `TRUSTED_PROXY_HOPS` | Number of proxy hops to parse client IP from right of `X-Forwarded-For` | `1` | `1 – 5` |
| `RATE_LIMIT_PER_MINUTE` | Per-client IP sliding-window rate limit | `10` | `1 – 600` |
| `RATE_LIMIT_GLOBAL_PER_MINUTE` | Global service-wide sliding-window rate limit | `120` | `1 – 10000` |
| `MAX_BODY_BYTES` | Maximum incoming payload size in bytes | `1048576` (1MB) | `1024 – 10485760` |

---

## 🔒 Operational Constraints & Known Limitations

- **Per-Instance Rate Limiting**: The sliding-window rate limiter is in-memory and operates per container instance.
- **Device-Bound Persistence**: Event plans are stored in browser `localStorage` under `eventpilot_active_plan_v1`.
- **Offline Generation**: Creating new plans requires connectivity to Vertex AI or the backend server.
