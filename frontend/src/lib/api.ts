const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchJobs(params: { q?: string; category?: string; min_score?: number; india_only?: boolean } = {}) {
  const query = new URLSearchParams();
  if (params.q) query.append("q", params.q);
  if (params.category) query.append("category", params.category);
  if (params.min_score) query.append("min_score", params.min_score.toString());
  if (params.india_only) query.append("india_only", "true");
  
  const res = await fetch(`${API_BASE}/jobs/?${query.toString()}`, { cache: "no-store" });
  return res.json();
}

export async function fetchJobDetail(id: number) {
  const res = await fetch(`${API_BASE}/jobs/${id}`, { cache: "no-store" });
  return res.json();
}

export async function triggerJobDiscovery(q: string = "") {
  const res = await fetch(`${API_BASE}/jobs/discover?query=${encodeURIComponent(q)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function fetchVerifiedCompanies() {
  const res = await fetch(`${API_BASE}/jobs/companies`, { cache: "no-store" });
  return res.json();
}

export async function prepareApplication(jobId: number) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/prepare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function fetchApplications(status?: string) {
  const url = status ? `${API_BASE}/applications/?status=${status}` : `${API_BASE}/applications/`;
  const res = await fetch(url, { cache: "no-store" });
  return res.json();
}

export async function fetchApplicationDetail(id: number) {
  const res = await fetch(`${API_BASE}/applications/${id}`, { cache: "no-store" });
  return res.json();
}

export async function approveApplication(id: number) {
  const res = await fetch(`${API_BASE}/applications/${id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function rejectApplication(id: number, reason: string = "Rejected by user") {
  const res = await fetch(`${API_BASE}/applications/${id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason })
  });
  return res.json();
}

export async function markAssistedSubmitted(id: number, confirmation_notes: string) {
  const res = await fetch(`${API_BASE}/applications/${id}/mark-submitted`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmation_notes })
  });
  return res.json();
}

export async function fetchCandidateProfile() {
  const res = await fetch(`${API_BASE}/resumes/profile`, { cache: "no-store" });
  return res.json();
}

export async function scanResumeFolder(folder_path: string) {
  const res = await fetch(`${API_BASE}/resumes/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder_path })
  });
  return res.json();
}

export async function parseResumeFile(file_path: string) {
  const res = await fetch(`${API_BASE}/resumes/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_path })
  });
  return res.json();
}

export async function fetchAnalyticsOverview() {
  const res = await fetch(`${API_BASE}/analytics/overview`, { cache: "no-store" });
  return res.json();
}

export async function fetchSettings() {
  const res = await fetch(`${API_BASE}/settings/`, { cache: "no-store" });
  return res.json();
}

export async function updateSettings(data: any) {
  const res = await fetch(`${API_BASE}/settings/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchTelegramStatus() {
  const res = await fetch(`${API_BASE}/telegram/status`, { cache: "no-store" });
  return res.json();
}

export async function sendTelegramTest(message: string) {
  const res = await fetch(`${API_BASE}/telegram/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  });
  return res.json();
}

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/audit/logs`, { cache: "no-store" });
  return res.json();
}

export async function fetchBatches(limit: number = 20) {
  const res = await fetch(`${API_BASE}/batches/?limit=${limit}`, { cache: "no-store" });
  return res.json();
}

export async function createBatch(targetSize: number = 25, category?: string) {
  const query = new URLSearchParams();
  query.append("target_size", targetSize.toString());
  if (category) query.append("category", category);
  const res = await fetch(`${API_BASE}/batches/create?${query.toString()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function fetchBatchDetail(batchId: string) {
  const res = await fetch(`${API_BASE}/batches/${batchId}`, { cache: "no-store" });
  return res.json();
}

export async function applyBatch(batchId: string, authorizedBy: string = "web_ui") {
  const res = await fetch(`${API_BASE}/batches/${batchId}/apply?authorized_by=${authorizedBy}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function pauseBatch(batchId: string) {
  const res = await fetch(`${API_BASE}/batches/${batchId}/pause`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function resumeBatch(batchId: string) {
  const res = await fetch(`${API_BASE}/batches/${batchId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function stopBatch(batchId: string) {
  const res = await fetch(`${API_BASE}/batches/${batchId}/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

