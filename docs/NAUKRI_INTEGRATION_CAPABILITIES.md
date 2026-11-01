# NAUKRI.COM INTEGRATION CAPABILITIES & FEASIBILITY REPORT
**Version:** 7.0  
**Status:** Canonical Reference Document  
**Date:** 2026-11-01  
**Author:** Principal AI Systems & Recruitment Platform Integration Specialist  

---

## 1. Executive Summary

This document establishes the official architectural baseline for integrating **Naukri.com** (Info Edge India Ltd) into the **Global Job Hunter AI** platform. It identifies legitimately supported integration avenues, analyzes platform constraints, and establishes strict compliance boundaries to safeguard user accounts, data privacy, and legal terms of service.

**Core Finding:**  
Naukri.com does **not** provide a public, unauthenticated, or third-party candidate submission REST API. Furthermore, Naukri's official **Naukri Neo** (and Naukri360 Pro) service operates strictly inside Naukri's proprietary internal ecosystem without third-party programmatic triggers. Consequently:
1. Candidate applications will **never** attempt undocumented private endpoints, automated browser scraping, cookie stealing, or CAPTCHA bypass.
2. The integration operates via **Assisted Application Preparation**, **Authorized Email Ingestion (Gmail OAuth 2.0)**, **User-Provided URL Discovery**, and **External Employer ATS Redirection**.
3. A formal `OFFICIAL_PARTNER_API` interface is provided and staged for instant activation if official Info Edge partner credentials are commissioned.

---

## 2. Integration Capabilities Matrix

| Functional Area | Availability | Official Endpoint / Protocol | Required Permissions | Rate Limits | Implementation Status | Supported Fallback |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Public Candidate Job Search API** | **UNAVAILABLE** | None publicly published for candidate-side bots | Info Edge Enterprise License | Unknown | Disabled by policy | User URL import + Gmail Alert Ingestion |
| **Direct Application Submission API** | **UNAVAILABLE (For 3rd-Party Bots)** | Recruiter ATS Webhook only (Greenhouse/Lever) | Employer ATS Partner Agreement | Bound to ATS agreement | Staged via `OFFICIAL_PARTNER_API` interface | Assisted Application Package + Portal Deep-Link |
| **Naukri Neo Auto-Apply Tracking** | **AUTHORIZED RECORD INGESTION** | Gmail OAuth 2.0 (Application receipts) | `gmail.readonly` | Google Cloud API Quotas | **ACTIVE** | Manual candidate confirmation |
| **Email Job Recommendation Alerts** | **AVAILABLE** | Gmail OAuth 2.0 (`@naukri.com`, `@naukrialerts.com`) | `gmail.readonly` | Google Cloud API Quotas | **ACTIVE** | Manual job link paste via Telegram |
| **Direct User URL Import** | **AVAILABLE** | Telegram `/naukri` bot commands & REST API | Owner Telegram ID | 60 requests/minute | **ACTIVE** | Native Telegram message handler |
| **Employer ATS Redirection** | **AVAILABLE** | Outbound HTTP redirect resolution | None (Public career URLs) | Standard HTTP backoff | **ACTIVE** | Phase 1 Greenhouse/Lever/Ashby Connectors |
| **Candidate Profile Optimization** | **AVAILABLE** | Local LLM Engine (TF-IDF + Gemini) | None (Local synthesis) | Bounded local LLM tokens | **ACTIVE** | Copyable profile update text blocks |
| **Naukri Account Scrape / Auto-Login** | **STRICTLY PROHIBITED** | N/A | Forbidden under Naukri Terms | N/A | **PROHIBITED** | Zero credential storage |

---

## 3. Detailed Investigation of Specific Areas

### 3.1 Public Jobseeker APIs
Naukri does not offer an open developer portal for candidate-side third-party applications. Info Edge provides APIs exclusively to B2B enterprise recruiters through the **Resdex API** suite and **eHierarchy** enterprise integrations. These endpoints are strictly recruiter-facing (candidate search, job posting creation, and resume downloads). Mistaking recruiter APIs for candidate submission endpoints violates security and architectural rules.

### 3.2 Naukri Neo & Naukri360 Pro
- **Nature of Service:** Naukri Neo is an in-house premium subscription service provided directly by Naukri to jobseekers. It automatically applies to qualifying recruiter postings using algorithms internal to Naukri.
- **API Availability:** Naukri Neo exposes **no public webhook or API** for external bots to initiate or command auto-applications.
- **Architectural Handling:** Our system treats Naukri Neo as an **independent application source (`NAUKRI_NEO`)**. When Naukri Neo submits an application, Naukri dispatches confirmation emails to the candidate's verified Gmail inbox. Global Job Hunter AI ingests these receipts via authorized OAuth, records the event in `naukri_neo_status_records`, links the application to canonical database records, and notifies Telegram—**without falsely claiming that our bot performed the submission**.

### 3.3 Email Alert Ingestion (Method B)
Naukri regularly dispatches structured job recommendations from verified sender addresses:
- `jobalerts@naukri.com`
- `alerts@naukri.com`
- `neo-updates@naukri.com`
- `mailer@naukri.com`

These messages contain vacancy titles, company names, location tags (Delhi NCR, Noida, Gurugram, Remote India), experience brackets, and direct job links. Global Job Hunter AI uses its existing Phase 6 Gmail service to safely parse these alerts into canonical `JobPosting` and `naukri_job_imports` records.

### 3.4 User-Provided Job Links (Method A)
Candidates can forward any Naukri vacancy URL (`https://www.naukri.com/job-listings-...`) to the Telegram bot or web dashboard. The system extracts the job ID and metadata, performs compatibility scoring against Mustkeem Ahmad's resume, and stages an application package.

### 3.5 External Employer ATS Redirections (Method D)
A significant percentage of high-value Indian tech roles listed on Naukri redirect to employer-hosted ATS instances (e.g., `boards.greenhouse.io`, `jobs.lever.co`, `jobs.ashbyhq.com`). When detected, the adapter classifies the capability as `EXTERNAL_ATS_APPLICATION` and executes or prepares the application using existing Phase 1–5 ATS connectors.

---

## 4. Platform Compliance & Security Rules

1. **Zero Credential Theft:** No Naukri usernames or passwords will be requested, stored, or processed.
2. **Zero Automated Account Impersonation:** No headless browsers (Puppeteer, Playwright, Selenium) will simulate user logins on Naukri.com.
3. **Transparent Record Provenance:** Every application record in the database maintains an immutable `application_source` tag (`NAUKRI_NEO`, `NAUKRI_MANUAL`, `EXTERNAL_ATS`, or `JOB_HUNTER_AUTHORIZED_AUTO`).
4. **Human Confirmation:** When preparing an application for a standard Naukri role, the user is provided a direct link to review and finalize submission.
