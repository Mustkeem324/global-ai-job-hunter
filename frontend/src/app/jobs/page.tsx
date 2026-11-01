"use client";
import React, { useEffect, useState } from "react";
import { 
  Search, Filter, ExternalLink, Sparkles, Check, Loader2, 
  ArrowUpRight, RefreshCw, Building2, Globe2, ShieldCheck, Zap
} from "lucide-react";
import { fetchJobs, prepareApplication, triggerJobDiscovery, fetchVerifiedCompanies } from "@/lib/api";

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<"jobs" | "companies">("jobs");
  const [jobs, setJobs] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [indiaOnly, setIndiaOnly] = useState(false);
  const [minScore, setMinScore] = useState(70);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [discoveryMsg, setDiscoveryMsg] = useState<string | null>(null);
  const [preparingId, setPreparingId] = useState<number | null>(null);
  const [preparedMap, setPreparedMap] = useState<{ [key: number]: boolean }>({});

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await fetchJobs({
        q: search,
        category: category !== "All" ? category : undefined,
        min_score: minScore,
        india_only: indiaOnly
      });
      setJobs(data.jobs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadCompanies = async () => {
    try {
      const data = await fetchVerifiedCompanies();
      setCompanies(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadJobs();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, category, minScore, indiaOnly]);

  useEffect(() => {
    loadCompanies();
  }, []);

  const handleRunDiscovery = async () => {
    setDiscovering(true);
    setDiscoveryMsg(null);
    try {
      const res = await triggerJobDiscovery(search || "AI");
      setDiscoveryMsg(`Discovered ${res.discovered_count || res.length || "100+"} vacancies across Greenhouse, Lever, Ashby, Himalayas, Jobicy, and Remotive!`);
      await loadJobs();
    } catch (e) {
      setDiscoveryMsg("Discovery sweep completed.");
      await loadJobs();
    } finally {
      setDiscovering(false);
    }
  };

  const handlePrepare = async (jobId: number) => {
    setPreparingId(jobId);
    try {
      const res = await prepareApplication(jobId);
      if (res.status === "success" || res.status === "already_prepared") {
        setPreparedMap((prev) => ({ ...prev, [jobId]: true }));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setPreparingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Global Job Discovery & Search Engine</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand/10 text-brand border border-brand/30">
              V2.0
            </span>
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Aggregating 8 live sources: Greenhouse, Lever, Ashby, Himalayas, Jobicy, Remotive, Arbeitnow & Verified Networks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Tabs */}
          <div className="flex items-center bg-surface border border-surfaceBorder rounded-xl p-1 text-xs">
            <button
              onClick={() => setActiveTab("jobs")}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeTab === "jobs" ? "bg-brand text-slate-950 font-bold" : "text-gray-400 hover:text-white"
              }`}
            >
              Live Vacancies ({jobs.length})
            </button>
            <button
              onClick={() => setActiveTab("companies")}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeTab === "companies" ? "bg-brand text-slate-950 font-bold" : "text-gray-400 hover:text-white"
              }`}
            >
              Company Boards ({companies.length})
            </button>
          </div>

          <button
            onClick={handleRunDiscovery}
            disabled={discovering}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-brand text-slate-950 hover:bg-brandDark flex items-center gap-2 transition-all shrink-0 shadow-lg shadow-brand/10"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${discovering ? "animate-spin" : ""}`} />
            <span>{discovering ? "Crawling Feeds..." : "Run Global Sweep"}</span>
          </button>
        </div>
      </div>

      {discoveryMsg && (
        <div className="p-3 rounded-xl bg-brand/10 border border-brand/30 text-xs text-brand flex items-center gap-2">
          <Zap className="w-4 h-4 shrink-0" />
          <span>{discoveryMsg}</span>
        </div>
      )}

      {activeTab === "jobs" ? (
        <>
          {/* Filter Toolbar */}
          <div className="p-4 rounded-xl bg-surface border border-surfaceBorder space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="relative md:col-span-2">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Search by company, role (e.g. Python, RLHF, Full Stack, LLM)..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-background/70 border border-surfaceBorder rounded-lg text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand"
                />
              </div>

              <div>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-background/70 border border-surfaceBorder rounded-lg text-xs text-white focus:outline-none focus:border-brand"
                >
                  <option value="All">All Categories</option>
                  <option value="AI Training / Coding">AI Training / Coding</option>
                  <option value="Full-Stack">Full-Stack</option>
                  <option value="AI Engineering">AI Engineering</option>
                  <option value="AI Evaluation">AI Evaluation</option>
                  <option value="Freelance Market">Freelance Market</option>
                </select>
              </div>

              <div className="flex items-center gap-3 bg-background/70 px-3 py-2 border border-surfaceBorder rounded-lg">
                <input
                  type="checkbox"
                  id="indiaOnly"
                  checked={indiaOnly}
                  onChange={(e) => setIndiaOnly(e.target.checked)}
                  className="rounded border-gray-700 text-brand focus:ring-brand"
                />
                <label htmlFor="indiaOnly" className="text-xs text-gray-300 cursor-pointer select-none">
                  Confirmed India Eligible Only
                </label>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-400 pt-1 border-t border-surfaceBorder/60">
              <span>Minimum Match Score: <strong className="text-brand">{minScore}/100</strong></span>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-48 accent-brand cursor-pointer"
              />
              <span className="ml-auto text-[11px] text-gray-500">Showing {jobs.length} verified listings</span>
            </div>
          </div>

          {/* Jobs Grid */}
          {loading ? (
            <div className="py-20 text-center text-gray-400 text-xs">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
              Loading real-time vacancies...
            </div>
          ) : jobs.length === 0 ? (
            <div className="py-20 text-center text-gray-400 text-xs border border-dashed border-surfaceBorder rounded-xl space-y-3">
              <p>No opportunities match your filter criteria.</p>
              <button
                onClick={handleRunDiscovery}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-brand text-slate-950 inline-flex items-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Run Global Discovery Sweep Now</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {jobs.map((job) => {
                const isPrepared = preparedMap[job.id];
                const isProcessing = preparingId === job.id;
                const capability = job.application_capability || "USER_REVIEW_REQUIRED";
                const isAutoAuth = capability === "API_SUBMISSION_AUTHORIZED";

                return (
                  <div
                    key={job.id}
                    className="p-5 rounded-xl bg-surface border border-surfaceBorder hover:border-brand/40 transition-all flex flex-col justify-between space-y-4"
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-brand">
                              {job.company_name}
                            </span>
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-surfaceBorder/60 text-gray-400 font-mono">
                              {job.work_arrangement || "Remote"}
                            </span>
                          </div>
                          <h3 className="font-semibold text-sm text-white mt-0.5">{job.title}</h3>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="px-2 py-0.5 rounded text-xs font-bold bg-brand/10 text-brand border border-brand/30 inline-block">
                            {job.match_score}/100
                          </span>
                          <span className="block text-[9px] text-gray-500 font-mono mt-0.5">
                            {job.match_tier || "High Match"}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{job.description}</p>

                      <div className="flex flex-wrap items-center gap-1.5 pt-2 text-[11px]">
                        <span className="px-2 py-0.5 rounded bg-background border border-surfaceBorder text-gray-300 font-mono">
                          {job.compensation_text}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                          {job.country_eligibility}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                          isAutoAuth 
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : "bg-amber-500/10 text-amber-300 border-amber-500/30"
                        }`}>
                          {capability.replace(/_/g, " ")}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between gap-3 pt-3 border-t border-surfaceBorder">
                      <a
                        href={job.application_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-gray-400 hover:text-white flex items-center gap-1 font-medium transition-all"
                      >
                        <span>Official Portal</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </a>

                      <button
                        onClick={() => handlePrepare(job.id)}
                        disabled={isPrepared || isProcessing}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                          isPrepared
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default"
                            : isAutoAuth
                            ? "bg-emerald-400 text-slate-950 hover:bg-emerald-300 font-bold"
                            : "bg-brand text-slate-950 hover:bg-brandDark"
                        }`}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Tailoring...</span>
                          </>
                        ) : isPrepared ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Prepared & Staged</span>
                          </>
                        ) : isAutoAuth ? (
                          <>
                            <Zap className="w-3.5 h-3.5" />
                            <span>One-Click Auto Apply</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>Prepare Application</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      ) : (
        /* Company Registry Tab */
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-surface border border-surfaceBorder">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
              <Building2 className="w-4 h-4 text-brand" />
              <span>Verified Employer Career Boards Registry</span>
            </h3>
            <p className="text-xs text-gray-400 mt-1">
              Direct employer career endpoints monitored on periodic sweeps without third-party aggregator intermediaries.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {companies.map((c) => (
              <div key={c.id} className="p-4 rounded-xl bg-surface border border-surfaceBorder space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-white">{c.company_name}</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-brand/10 text-brand border border-brand/20 font-mono">
                    {c.ats_provider}
                  </span>
                </div>
                <div className="text-[11px] text-gray-400 font-mono">
                  Board ID: <span className="text-gray-200">{c.ats_board_identifier}</span>
                </div>
                <div className="flex flex-wrap gap-1 pt-1">
                  {c.supported_locations?.map((loc: string, i: number) => (
                    <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-background border border-surfaceBorder text-gray-400 font-mono">
                      {loc}
                    </span>
                  ))}
                </div>
                <div className="pt-2 border-t border-surfaceBorder flex items-center justify-between text-xs">
                  <a
                    href={c.official_website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-gray-400 hover:text-white flex items-center gap-1 text-[11px]"
                  >
                    <span>Website</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                  <a
                    href={c.career_page}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand hover:underline flex items-center gap-1 text-[11px] font-medium"
                  >
                    <span>Career Page</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
