# AGENTS.md — Global Job Hunter Autonomous Agent Architecture

## 1. System Overview
Global Job Hunter AI is an agentic employment automation platform structured into specialized, bounded worker agents. Each agent operates under strict least-privilege boundaries, with deterministic state machines and compliance guardrails.

---

## 2. Agent Catalog & Roles

### Agent 1: Job Discovery Agent (`discovery_worker`)
* **Role:** Modular connector polling official employer career portals, public ATS endpoints (Greenhouse, Lever, Ashby), and remote feeds (Remotive, RemoteOK).
* **Schedule:** Runs every 6 hours or on user demand.
* **Output:** Normalized canonical job schema with deduplication keys (`company:title`).

### Agent 2: Eligibility & Verification Agent (`verification_worker`)
* **Role:** Validates vacancy active status, verifies work authorization policies (100% confirmed India-eligible or Worldwide), and detects geographic restrictions.
* **Security Guardrail:** Neutralizes prompt-injection payloads embedded within untrusted job postings.

### Agent 3: Resume Matching & Scoring Agent (`matching_engine`)
* **Role:** Evaluates candidate fit across 6 deterministic dimensions:
  1. Technical Skills Match: **30%**
  2. Demonstrable Experience: **20%**
  3. Work Authorization / India Remote Eligibility: **20%**
  4. Role Requirements & Education: **10%**
  5. Employment Preferences: **10%**
  6. Recency & Opportunity Quality: **10%**
* **Output:** Compatibility score (0–100) with detailed evidence breakdown.

### Agent 4: Application Document Synthesis Agent (`document_generator`)
* **Role:** Generates tailored professional summaries, ATS headlines, concise cover letters, and truthful standard application answers.
* **Strict Factuality Rule:** Uses only verified facts extracted from the candidate's actual resume (e.g. Handshake Project Dynamo, Outlier AI, FreelanceKar 200+ projects). Never invents credentials.

### Agent 5: State Machine & Execution Engine (`application_executor`)
* **Role:** Governs application state transitions according to configured modes:
  * **Mode A (Fully Autonomous):** Restricted strictly to allowed sources.
  * **Mode B (Approval Required):** Default safe workflow staging applications in queue.
  * **Mode C (Assisted Mode):** Prepares form-filling payloads for user-guided completion on restricted portals.
* **Evidence Verification:** Demands authoritative confirmation receipts (`confirmation_id`). A browser click alone is never accepted as evidence.

### Agent 6: Telegram Notification Agent (`telegram_service`)
* **Role:** Real-time event alerts via Telegram Bot API for high-match roles (≥90/100), staged approval requests, and confirmed submission receipts.

---

## 3. Threat Model & Security Controls
* **SSRF Protection:** Resolves hostnames and rejects private loopback addresses (RFC 1918, `127.0.0.1`, `::1`).
* **Prompt Injection Defense:** Scans job listings for jailbreak patterns (`ignore previous instructions`, `bypass filters`).
* **Anti-Spam Governors:** Enforces daily limits (max 10 submissions/day) and minimum 30-day cooling-off periods per company.
