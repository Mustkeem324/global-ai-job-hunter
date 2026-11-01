# GLOBAL JOB HUNTER AI — CLOUD DEPLOYMENT & OPERATIONS MANUAL
**Platform Version:** 4.0.0-PROD  
**Document Classification:** Production Architecture & Operational Runbook  

---

## 1. ARCHITECTURE OVERVIEW

Global Job Hunter AI is engineered for resilient, 24/7 continuous operation independently of local IDE environments. The system executes automated job discovery across 8 global ATS feeds, intelligent opportunity prioritization (Priority A–D), resume tailoring with zero hallucination enforcement, verifiable one-click Telegram application orchestration, and Gmail employer response monitoring.

---

## 2. DEPLOYMENT PROFILE A — UBUNTU VPS (RECOMMENDED SELF-HOSTED)

### Prerequisites
- Clean Ubuntu 22.04 / 24.04 LTS VPS (Minimum 2 vCPU, 4GB RAM, 20GB SSD)
- Docker Engine 24+ & Docker Compose v2+ installed
- Domain name with DNS A records pointing to the VPS IP
- Telegram Bot Token obtained from `@BotFather`

### Step-by-Step Setup
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Mustkeem324/global-ai-job-hunter.git
   cd global-ai-job-hunter
   ```

2. **Configure Environment Secrets:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Required variables to set:*
   - `TELEGRAM_BOT_TOKEN`: Your verified bot token
   - `TELEGRAM_CHAT_ID`: Your personal or group chat ID
   - `TELEGRAM_OWNER_ID`: Your numerical Telegram user ID (enforces privileged operations)
   - `GEMINI_API_KEY`: API key for model-assisted evaluation
   - `AUTO_APPLY_ENABLED`: Set to `false` initially for supervised safety

3. **Deploy Containerized Services:**
   ```bash
   docker compose up -d --build
   ```

4. **Verify Container Health:**
   ```bash
   docker compose ps
   docker compose logs -f backend
   ```
   Services running:
   - `jobhunter_postgres`: Port 5432 (Healthchecked)
   - `jobhunter_redis`: Port 6379 (Healthchecked)
   - `jobhunter_backend`: Port 8000 (FastAPI API + Scheduler + Telegram Poller)
   - `jobhunter_frontend`: Port 3000 (Next.js Responsive Dashboard)

5. **Execute Automated Backup Test:**
   ```bash
   ./backend/scripts/backup_and_restore.sh
   ```

---

## 3. DEPLOYMENT PROFILE B — MANAGED CLOUD (GOOGLE CLOUD RUN & CLOUD SQL)

### Architecture
- **Stateless Web & API:** Google Cloud Run service (Auto-scaling 1 to 5 instances)
- **Database:** Google Cloud SQL for PostgreSQL (db-f1-micro or db-g1-small)
- **Message Broker:** Managed Memorystore for Redis or Cloud Tasks
- **Scheduled Jobs:** Google Cloud Scheduler invoking Cloud Run jobs for 3h/6h sweeps
- **Secrets:** Google Cloud Secret Manager for credentials
- **Storage:** Google Cloud Storage for versioned resumes and submission receipts

### Deployment Steps
1. **Authenticate and configure project:**
   ```bash
   gcloud auth login
   gcloud config set project [YOUR_GCP_PROJECT_ID]
   ```

2. **Store Secrets in Secret Manager:**
   ```bash
   gcloud secrets create jobhunter-telegram-token --data-file=- <<< "$TELEGRAM_BOT_TOKEN"
   gcloud secrets create jobhunter-gemini-key --data-file=- <<< "$GEMINI_API_KEY"
   ```

3. **Deploy Backend to Cloud Run:**
   ```bash
   gcloud run deploy jobhunter-backend \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars TIMEZONE="Asia/Kolkata",APP_ENV="production"
   ```

4. **Schedule Discovery Cron in Cloud Scheduler:**
   ```bash
   gcloud scheduler jobs create http jobhunter-discovery-sweep \
     --schedule="0 */6 * * *" \
     --uri="https://[YOUR_CLOUD_RUN_URL]/api/v1/jobs/sweep" \
     --http-method=POST
   ```

---

## 4. TELEGRAM OPERATIONS CONTROL COMMANDS

| Command | Function |
| :--- | :--- |
| `/operations` | System operational dashboard (scheduler, workers, DB latency, uptime) |
| `/priority` | Displays top Priority A vacancies (Score ≥ 85) with one-click actions |
| `/queue` or `/pending` | Displays applications staged for candidate authorization |
| `/followups` | Lists context-aware follow-up email drafts awaiting approval |
| `/interviews` | Displays active interview pipeline and upcoming deadlines |
| `/today` | Generates today's operational activity digest |
| `/weekly` | Generates weekly conversion rate and pipeline summary |
| `/sourcehealth` | Live latency and circuit-breaker status of all 8 ATS feeds |
| `/errors` | Recent error and rejection diagnostics |
| `/pause_jobs` | Suspends automated background crawler schedules |
| `/resume_jobs` | Resumes automated crawler schedules |
| `/emergency_stop` | **Immediate safety kill-switch:** disarms auto-apply and halts all pending submissions |
| `/settings` | Real-time threshold adjustments and India-only filter toggle |

---

## 5. COST & RESOURCE OPTIMIZATION POLICY

- **AI Token Control:** Deterministic rule engines filter unviable jobs and map standard form fields *before* invoking LLM calls.
- **Daily Budget Cap:** `MAX_DAILY_AI_COST_USD=5.0` automatically prevents unexpected API overages.
- **Circuit Breakers:** Feeds with >5 consecutive network failures are paused for 30 minutes to protect external rate limits.
- **Deduplication:** Jobs are checked via canonical source IDs; unchanged vacancies are never reprocessed.
