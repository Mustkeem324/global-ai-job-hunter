# Global Job Hunter AI — Autonomous Employment Platform

![Global AI Job Hunter Banner](assets/banner.png)

[![Platform](https://img.shields.io/badge/Platform-Full--Stack%20Autonomous%20System-blue.svg)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20SQLAlchemy%20%7C%20Pydantic-brightgreen.svg)](#)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20%7C%20Tailwind%20CSS%20%7C%20TypeScript-blue.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-11%2F11%20Passing-success.svg)](#)
[![India Eligibility](https://img.shields.io/badge/Eligibility-100%25%20India%20Confirmed-orange.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#)

---

## Visual Career Architecture & Pathways

![Career Pathways Architecture](assets/career_architecture.png)

---

## 🌟 Executive Overview

**Global Job Hunter AI** is a production-grade, self-hostable autonomous AI job searching, matching, application preparation, and monitoring platform designed specifically for technical candidates based in India targeting international and domestic opportunities in:
* **AI Training & RLHF (Outlier, Alignerr, Surge AI, Mercor, Handshake, Mindrift)**
* **Full-Stack Software Engineering (Python, Django, FastAPI, React, Next.js, Node.js)**
* **Global Freelance & Consulting (Contra, Braintrust, Upwork Enterprise, Lemon.io)**
* **Remote AI Systems & EOR Employment (HTTPie, Bloomreach, Weekday, INFUSE)**

---

## ⚡ The 3 Application Modes

The platform strictly enforces three application modes:

### 1. MODE A: FULLY AUTOMATIC
* **Condition:** Enabled only for individually authorized sources in your allowlist (e.g. `mock_ats`, `greenhouse_sandbox`).
* **Workflow:** Discovers active job -> verifies eligibility -> calculates match -> generates tailored application -> submits through permitted API -> verifies authoritative receipt (`confirmation_id`) -> logs audit trail -> delivers instant Telegram notification.
* **Compliance Guard:** Explicit user consent required in settings. Never circumvents CAPTCHA, bot checks, or website terms.

### 2. MODE B: APPROVAL REQUIRED (Default Safe Mode)
* **Workflow:** Automatically discovers and scores positions, drafts personalized cover letters and tailored ATS summaries, and stages them in your **Application Queue**.
* **Action:** You review the documents in the dashboard and click **"Approve & Authorize"** or **"Reject"**. Submission only proceeds upon explicit user action.

### 3. MODE C: ASSISTED APPLICATION
* **Workflow:** For third-party platforms that prohibit automation (e.g. Workday, Lever, Greenhouse web forms).
* **Action:** Provides direct official application URLs, prepares pre-filled factual answer templates, and logs your manual submission confirmation note into the audit database.

---

## 🏗️ Architecture & Technology Stack

```
global-ai-job-hunter/
├── backend/                      # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                  # RESTful API Endpoints
│   │   │   ├── routes_jobs.py          # Job Discovery, Filtering & Preparation
│   │   │   ├── routes_resumes.py       # Resume Folder Ingestion & Parsing
│   │   │   ├── routes_applications.py  # Application Queue & State Machine
│   │   │   ├── routes_settings.py      # Automation Policies & Thresholds
│   │   │   ├── routes_telegram.py      # Real Telegram Bot API Alerts
│   │   │   ├── routes_analytics.py     # Conversion Funnels & Metrics
│   │   │   └── routes_audit.py         # Immutable Audit Event Logs
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings & Environment
│   │   │   ├── database.py             # SQLAlchemy Engine & Session Factory
│   │   │   ├── security.py             # SSRF Whitelist & Prompt Injection Filter
│   │   │   └── state_machine.py        # Strict Application State Machine
│   │   ├── models/
│   │   │   └── schema.py               # 15 Normalized Database Tables
│   │   ├── services/
│   │   │   ├── resume_parser.py        # PDF/DOCX Parsing with Evidence Extraction
│   │   │   ├── matching_engine.py      # 6-Factor 0-100 Compatibility Engine
│   │   │   ├── document_generator.py   # Tailored Cover Letters & Factual Answers
│   │   │   ├── discovery_service.py    # Modular Job Source Connectors
│   │   │   ├── application_executor.py # Mode A/B/C Submission Handlers
│   │   │   ├── telegram_service.py     # Real Telegram Webhook Client
│   │   │   └── scheduler_service.py    # APScheduler Background Workers (6h cycle)
│   │   └── main.py                     # FastAPI App Factory & Lifespan
│   ├── tests/                          # Pytest Automated Test Suite
│   └── requirements.txt
├── frontend/                     # Next.js 14 Dashboard
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                # Real-Time Overview & KPIs
│   │   │   ├── jobs/page.tsx           # Interactive Job Explorer & Search
│   │   │   ├── queue/page.tsx          # Application Review & Approval Queue
│   │   │   ├── history/page.tsx        # Submitted Timeline & Receipts
│   │   │   ├── resumes/page.tsx        # Folder Ingestion & Skill Matrix
│   │   │   ├── settings/page.tsx       # Mode A/B Policy & Threshold Toggles
│   │   │   ├── notifications/page.tsx  # Telegram Bot Test & Event Hooks
│   │   │   ├── analytics/page.tsx      # Compensation Bands & Funnels
│   │   │   └── security/page.tsx       # Security Posture & State Logs
│   │   ├── components/                 # Sidebar, Navbar, Stat Cards
│   │   └── lib/api.ts                  # Typed Frontend API Client
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── database/                     # Verified Curated Datasets
│   ├── opportunities.json
│   └── opportunities.csv
├── docker-compose.yml            # Multi-Container Deployment
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
├── AGENTS.md                     # Agent Protocol & Boundaries
└── ARCHITECTURE.md               # Technical Design Specification
```

---

## 🚀 Quickstart & Local Installation

### 1. Clone & Setup Environment
```bash
git clone https://github.com/Mustkeem324/global-ai-job-hunter.git
cd global-ai-job-hunter
cp .env.example .env
```

### 2. Run Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run Frontend (Next.js Dashboard)
```bash
cd frontend
npm install
npm run dev
```
* **Dashboard URL:** [http://localhost:3000](http://localhost:3000)

### 4. Run with Docker Compose
```bash
docker-compose up --build
```

---

## 🧪 Automated Test Suite

All 11 automated test suites execute against real database engines and verify parser accuracy, scoring weights, state machine transitions, and submission receipts:
```bash
cd backend
python3 -m pytest tests/ -v
```

```text
tests/test_api_endpoints.py::test_health_check PASSED
tests/test_api_endpoints.py::test_get_jobs PASSED
tests/test_api_endpoints.py::test_get_candidate_profile PASSED
tests/test_api_endpoints.py::test_analytics_overview PASSED
tests/test_application_executor.py::test_executor_mode_evaluation PASSED
tests/test_application_executor.py::test_executor_submission_mock_confirmation PASSED
tests/test_matching_engine.py::test_matching_engine_high_match PASSED
tests/test_matching_engine.py::test_matching_engine_restricted_job PASSED
tests/test_resume_parser.py::test_resume_parser_profile_extraction PASSED
tests/test_state_machine.py::test_valid_state_transitions PASSED
tests/test_state_machine.py::test_invalid_state_transitions PASSED
======================== 11 passed in 0.81s ========================
```

---

## 📱 Telegram Bot Setup

To receive instant alerts for high-match jobs (≥90/100) and application confirmations:
1. Message `@BotFather` on Telegram to create a bot and get your `TELEGRAM_BOT_TOKEN`.
2. Message `@userinfobot` to get your numeric `TELEGRAM_CHAT_ID`.
3. Add them to your `.env` or configure them in the dashboard under **Notifications**.
4. Click **"Send Test"** on the Notifications page to verify delivery.

---

## 🛡️ Security & Privacy Guardrails

* **Zero Credential Leakage:** Sensitive tokens are kept exclusively in server environment variables.
* **SSRF Protection:** External redirects and webhook destinations are validated to block private and loopback IP routing (`127.0.0.1`, RFC1918).
* **Adversarial Injection Filtering:** Untrusted job postings are filtered to strip prompt injection payloads.
* **Authoritative Evidence Standard:** Applications are never marked confirmed without verifiable receipts.
* **Data Sovereignty:** Resumes remain inside your designated workspace folder.

---

*Authored by [Mustkeem Ahmad](https://github.com/Mustkeem324) • Production Release November 2026*
