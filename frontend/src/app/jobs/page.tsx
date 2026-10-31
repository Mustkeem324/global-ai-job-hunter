"use client";
import React, { useEffect, useState } from "react";
import { Search, Filter, ExternalLink, Sparkles, Check, Loader2, ArrowUpRight } from "lucide-react";
import { fetchJobs, prepareApplication } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [indiaOnly, setIndiaOnly] = useState(false);
  const [minScore, setMinScore] = useState(70);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    const timer = setTimeout(() => {
      loadJobs();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, category, minScore, indiaOnly]);

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
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Global Job Explorer</h2>
        <p className="text-xs text-gray-400">
          Discover verified opportunities matching your background. Click 'Prepare Application' to generate tailored documents.
        </p>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-xl bg-surface border border-surfaceBorder space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="relative md:col-span-2">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by company, role (e.g. Python, RLHF, Full Stack)..."
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
          Loading opportunities...
        </div>
      ) : jobs.length === 0 ? (
        <div className="py-20 text-center text-gray-400 text-xs border border-dashed border-surfaceBorder rounded-xl">
          No opportunities match your filter criteria. Try adjusting the score threshold or search query.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job) => {
            const isPrepared = preparedMap[job.id];
            const isProcessing = preparingId === job.id;

            return (
              <div
                key={job.id}
                className="p-5 rounded-xl bg-surface border border-surfaceBorder hover:border-brand/40 transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                        {job.company_name}
                      </span>
                      <h3 className="font-semibold text-sm text-white">{job.title}</h3>
                    </div>
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-brand/10 text-brand border border-brand/30 shrink-0">
                      {job.match_score}/100
                    </span>
                  </div>

                  <p className="text-xs text-gray-400 line-clamp-2">{job.description}</p>

                  <div className="flex flex-wrap items-center gap-2 pt-2 text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-background border border-surfaceBorder text-gray-300 font-mono">
                      {job.compensation_text}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-background border border-surfaceBorder text-gray-300">
                      {job.work_arrangement}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {job.country_eligibility}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 pt-3 border-t border-surfaceBorder">
                  <a
                    href={job.application_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-gray-400 hover:text-white flex items-center gap-1 font-medium"
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
                        <span>Prepared & Queued</span>
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
    </div>
  );
}
