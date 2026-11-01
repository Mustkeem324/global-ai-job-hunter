"use client";
import React, { useEffect, useState } from "react";
import { 
  MapPin, 
  Send, 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  ExternalLink, 
  Copy, 
  RefreshCw, 
  Layers, 
  Bot, 
  Briefcase,
  ShieldCheck,
  FileText
} from "lucide-react";
import { 
  fetchNaukriCapabilities, 
  fetchNaukriHealth, 
  importNaukriUrl, 
  prepareNaukriJob, 
  prepareNaukriBatch, 
  fetchNaukriProfilePackage, 
  fetchNaukriNeoSettings, 
  updateNaukriNeoSettings, 
  fetchNaukriNeoRecords, 
  fetchJobs 
} from "@/lib/api";

export default function NaukriPage() {
  const [activeTab, setActiveTab] = useState<"jobs" | "optimizer" | "neo">("jobs");
  const [loading, setLoading] = useState(true);
  const [inputUrl, setInputUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  const [capabilities, setCapabilities] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [profilePkg, setProfilePkg] = useState<any>(null);
  const [neoSettings, setNeoSettings] = useState<any>({ is_neo_enabled: false, is_naukri360_pro: false });
  const [neoRecords, setNeoRecords] = useState<any[]>([]);
  const [prepModalData, setPrepModalData] = useState<any>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [caps, jobsData, profData, neoSetData, neoRecData] = await Promise.all([
        fetchNaukriCapabilities(),
        fetchJobs({ category: "AI Training & Evaluation", india_only: true }),
        fetchNaukriProfilePackage(),
        fetchNaukriNeoSettings(),
        fetchNaukriNeoRecords()
      ]);
      setCapabilities(caps);
      setJobs(jobsData.jobs || []);
      setProfilePkg(profData);
      setNeoSettings(neoSetData);
      setNeoRecords(neoRecData.records || []);
    } catch (e) {
      console.error("Error loading Naukri data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleImportUrl = async () => {
    if (!inputUrl.trim()) return;
    setImporting(true);
    setImportResult(null);
    try {
      const res = await importNaukriUrl(inputUrl.trim());
      setImportResult(res);
      setInputUrl("");
      await loadData();
    } catch (err: any) {
      setImportResult({ success: false, message: err.message || "Failed to import URL" });
    } finally {
      setImporting(false);
    }
  };

  const handlePrepareJob = async (jobId: number) => {
    try {
      const pkg = await prepareNaukriJob(jobId);
      setPrepModalData(pkg);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleNeo = async () => {
    const newVal = !neoSettings.is_neo_enabled;
    try {
      const res = await updateNaukriNeoSettings(newVal, neoSettings.is_naukri360_pro);
      setNeoSettings({ ...neoSettings, is_neo_enabled: newVal });
    } catch (e) {
      console.error(e);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-surface via-surface to-brand/10 border border-surfaceBorder p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium bg-brand/10 text-brand border border-brand/20">
            <MapPin className="w-3.5 h-3.5" />
            PHASE 7 — NAUKRI.COM INDIA RECRUITMENT ENGINE
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Naukri Discovery, Profile Optimizer & Neo Tracking
          </h1>
          <p className="text-sm text-gray-400 max-w-2xl leading-relaxed">
            Ingest Indian tech and AI opportunities directly from Naukri links and email alerts, optimize your profile headline and skills for the Naukri search algorithm, and track official Naukri Neo auto-applications.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-surface border border-surfaceBorder hover:border-gray-500 text-gray-300 hover:text-white text-xs font-semibold flex items-center gap-2 transition-all self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* URL Ingestion Box */}
      <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-3 shadow-sm">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-300 flex items-center gap-2">
          <Send className="w-3.5 h-3.5 text-brand" />
          <span>Import Naukri Vacancy URL</span>
        </h3>
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="Paste Naukri job link (e.g., https://www.naukri.com/job-listings-ai-engineer-...)"
            className="flex-1 w-full bg-background/80 border border-surfaceBorder rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand transition-colors"
          />
          <button
            onClick={handleImportUrl}
            disabled={importing || !inputUrl.trim()}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand to-accent text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-brand/20 transition-all disabled:opacity-50"
          >
            {importing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>Import & Match</span>
          </button>
        </div>

        {importResult && (
          <div className={`p-3.5 rounded-xl text-xs border ${importResult.success ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300" : "bg-red-500/10 border-red-500/20 text-red-300"}`}>
            {importResult.success ? (
              <div className="flex items-center justify-between">
                <span>
                  <b>Successfully Imported:</b> {importResult.company} — {importResult.title} ({importResult.match_score}% MATCH)
                </span>
                <button
                  onClick={() => handlePrepareJob(importResult.job_id)}
                  className="px-2.5 py-1 rounded bg-brand/20 text-brand text-[11px] font-semibold hover:bg-brand/30 transition-colors"
                >
                  Prepare Package
                </button>
              </div>
            ) : (
              <span>⚠️ {importResult.message}</span>
            )}
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-surfaceBorder pb-3 overflow-x-auto text-xs font-medium">
        {[
          { key: "jobs", label: `India & Naukri Openings (${jobs.length})`, icon: Briefcase },
          { key: "optimizer", label: "Naukri Profile Optimizer", icon: Sparkles },
          { key: "neo", label: `Naukri Neo Tracking (${neoRecords.length})`, icon: Bot }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap ${
                isActive
                  ? "bg-brand/10 text-brand border border-brand/30 shadow-sm"
                  : "text-gray-400 hover:text-white hover:bg-surfaceBorder/40"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: OPENINGS */}
      {activeTab === "jobs" && (
        <div className="space-y-3">
          {jobs.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-xs bg-surface border border-surfaceBorder rounded-2xl">
              No India-eligible vacancies found. Paste a Naukri URL above to import one.
            </div>
          ) : (
            jobs.map((j) => (
              <div key={j.id} className="p-5 rounded-2xl bg-surface border border-surfaceBorder flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-white text-sm">{j.title}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-background border border-surfaceBorder text-gray-300">
                      {j.company_name}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand/10 text-brand">
                      {j.match_score || 88}% MATCH
                    </span>
                  </div>
                  <div className="text-gray-400 text-[11px] flex items-center gap-3">
                    <span>📍 {j.location}</span>
                    <span>💰 {j.compensation_text}</span>
                    <span>Source: {j.source_id.toUpperCase()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handlePrepareJob(j.id)}
                    className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand to-accent text-white text-xs font-semibold shadow-sm flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Prepare Application</span>
                  </button>
                  <a
                    href={j.application_url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-surfaceBorder/40 transition-colors border border-surfaceBorder"
                    title="Open on Naukri"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 2: PROFILE OPTIMIZER */}
      {activeTab === "optimizer" && profilePkg && (
        <div className="space-y-6">
          {/* Headline Card */}
          <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white uppercase tracking-wider">
                Optimized Resume Headline ({profilePkg.headline_char_count}/250 chars)
              </span>
              <button
                onClick={() => copyToClipboard(profilePkg.recommended_headline, "headline")}
                className="text-xs text-brand hover:text-white flex items-center gap-1 transition-colors"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copiedKey === "headline" ? "Copied!" : "Copy"}</span>
              </button>
            </div>
            <div className="p-3.5 rounded-xl bg-background/60 border border-surfaceBorder font-mono text-xs text-gray-200">
              {profilePkg.recommended_headline}
            </div>
            <p className="text-[11px] text-gray-400">
              Tailored specifically to maximize recruiter keyword indexing for AI Training, RLHF, and Full-Stack searches.
            </p>
          </div>

          {/* Key Skills Tags Card */}
          <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white uppercase tracking-wider">
                Key Skills (Naukri Comma-Separated Format)
              </span>
              <button
                onClick={() => copyToClipboard(profilePkg.key_skills_csv, "skills")}
                className="text-xs text-brand hover:text-white flex items-center gap-1 transition-colors"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copiedKey === "skills" ? "Copied!" : "Copy Tags"}</span>
              </button>
            </div>
            <div className="p-3.5 rounded-xl bg-background/60 border border-surfaceBorder font-mono text-xs text-brand">
              {profilePkg.key_skills_csv}
            </div>
          </div>

          {/* Summary & Preferences Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-2">
              <span className="text-xs font-semibold text-white uppercase tracking-wider">Profile Summary</span>
              <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-line">
                {profilePkg.profile_summary}
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-3">
              <span className="text-xs font-semibold text-white uppercase tracking-wider">Verified Preferences</span>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between p-2.5 rounded-lg bg-background/50 border border-surfaceBorder">
                  <span className="text-gray-400">Notice Period:</span>
                  <span className="font-semibold text-white">{profilePkg.notice_period}</span>
                </div>
                <div className="flex justify-between p-2.5 rounded-lg bg-background/50 border border-surfaceBorder">
                  <span className="text-gray-400">Target Locations:</span>
                  <span className="font-semibold text-white">{profilePkg.preferred_locations?.join(", ")}</span>
                </div>
                <div className="flex justify-between p-2.5 rounded-lg bg-background/50 border border-surfaceBorder">
                  <span className="text-gray-400">Expected CTC:</span>
                  <span className="font-semibold text-white">{profilePkg.expected_ctc}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: NEO TRACKING */}
      {activeTab === "neo" && (
        <div className="space-y-5">
          {/* Neo Configuration Toggle Card */}
          <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-brand" />
                <h3 className="text-sm font-bold text-white">Naukri Neo & Naukri360 Pro Auto-Apply Tracking</h3>
              </div>
              <p className="text-xs text-gray-400 max-w-xl">
                Automatically reconcile and track applications dispatched by Naukri's official Neo service by parsing confirmation emails from your authorized Gmail account.
              </p>
            </div>

            <button
              onClick={handleToggleNeo}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                neoSettings.is_neo_enabled
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-surfaceBorder/60 hover:bg-surfaceBorder text-gray-300 border border-surfaceBorder"
              }`}
            >
              {neoSettings.is_neo_enabled ? "🟢 Neo Tracking Active" : "⚪ Neo Tracking Disabled"}
            </button>
          </div>

          {/* Neo Applications List */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Tracked Neo Applications ({neoRecords.length})
            </h4>
            {neoRecords.length === 0 ? (
              <div className="p-10 text-center text-gray-500 text-xs bg-surface border border-surfaceBorder rounded-2xl">
                No Naukri Neo applications detected yet. When Neo auto-applies on your behalf, confirmation emails will be ingested here.
              </div>
            ) : (
              neoRecords.map((r) => (
                <div key={r.id} className="p-4 rounded-xl bg-surface border border-surfaceBorder flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-white">{r.company_name} — {r.job_title}</div>
                    <div className="text-[11px] text-gray-400 mt-0.5">Applied on: {new Date(r.applied_at).toLocaleDateString()}</div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    {r.source}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* PREPARATION MODAL */}
      {prepModalData && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-surfaceBorder rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-surfaceBorder pb-4">
              <div>
                <h2 className="text-base font-bold text-white">Naukri Application Package Prepared</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  {prepModalData.title} at {prepModalData.company}
                </p>
              </div>
              <button
                onClick={() => setPrepModalData(null)}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surfaceBorder"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Screening Answers */}
            <div className="p-4 rounded-xl bg-background/50 border border-surfaceBorder space-y-2 text-xs">
              <span className="font-semibold text-white">Verified Screening Answers:</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-gray-300">
                <div><b>Notice Period:</b> {prepModalData.screening_answers?.notice_period}</div>
                <div><b>Location:</b> {prepModalData.screening_answers?.current_location}</div>
                <div><b>Total Experience:</b> {prepModalData.screening_answers?.total_experience}</div>
                <div><b>Relocation:</b> {prepModalData.screening_answers?.relocation_willingness}</div>
              </div>
            </div>

            {/* Cover Letter */}
            {prepModalData.cover_letter_text && (
              <div className="space-y-2 text-xs">
                <span className="font-semibold text-white">Tailored Cover Letter:</span>
                <div className="p-3.5 rounded-xl bg-background/40 border border-surfaceBorder text-gray-300 max-h-40 overflow-y-auto font-mono text-[11px] whitespace-pre-line">
                  {prepModalData.cover_letter_text}
                </div>
              </div>
            )}

            {/* Action Bar */}
            <div className="flex items-center justify-between pt-3 border-t border-surfaceBorder">
              <span className="text-xs text-gray-400 font-mono">
                Capability: {prepModalData.capability}
              </span>
              <a
                href={prepModalData.application_url}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand to-accent text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand/20 transition-all"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Open Naukri Portal to Submit</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
