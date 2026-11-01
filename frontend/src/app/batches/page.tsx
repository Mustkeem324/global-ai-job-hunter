"use client";
import React, { useEffect, useState } from "react";
import { 
  Layers, 
  Play, 
  Pause, 
  StopCircle, 
  RefreshCw, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Sparkles, 
  ExternalLink,
  ShieldCheck,
  Send,
  Zap,
  Filter
} from "lucide-react";
import { 
  fetchBatches, 
  createBatch, 
  fetchBatchDetail, 
  applyBatch, 
  pauseBatch, 
  resumeBatch, 
  stopBatch 
} from "@/lib/api";

const PRIORITY_CATEGORIES = [
  "All Priority Categories",
  "AI Training & Evaluation",
  "Python AI Agent Developer",
  "Full Stack Engineer",
  "Backend Python Systems",
  "Frontend Next.js Engineer",
  "Machine Learning Operations (MLOps)"
];

export default function BatchesPage() {
  const [batches, setBatches] = useState<any[]>([]);
  const [selectedBatch, setSelectedBatch] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [creatingSize, setCreatingSize] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("All Priority Categories");

  const loadBatches = async (autoSelectId?: string) => {
    setLoading(true);
    try {
      const data = await fetchBatches(20);
      const list = data.batches || [];
      setBatches(list);
      
      const targetId = autoSelectId || (selectedBatch ? selectedBatch.batch_id : (list.length > 0 ? list[0].batch_id : null));
      if (targetId) {
        await selectBatchById(targetId);
      } else {
        setSelectedBatch(null);
      }
    } catch (e) {
      console.error("Failed to load batches:", e);
    } finally {
      setLoading(false);
    }
  };

  const selectBatchById = async (batchId: string) => {
    setDetailLoading(true);
    try {
      const detail = await fetchBatchDetail(batchId);
      setSelectedBatch(detail);
    } catch (e) {
      console.error("Failed to load batch detail:", e);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const handleCreateBatch = async (size: number) => {
    setCreatingSize(size);
    try {
      const categoryParam = selectedCategory === "All Priority Categories" ? undefined : selectedCategory;
      const res = await createBatch(size, categoryParam);
      if (res && res.batch_id) {
        await loadBatches(res.batch_id);
      }
    } catch (e) {
      console.error("Failed to create batch:", e);
    } finally {
      setCreatingSize(null);
    }
  };

  const handleApplyBatch = async () => {
    if (!selectedBatch) return;
    setActionLoading(true);
    try {
      await applyBatch(selectedBatch.batch_id, "web_dashboard_admin");
      await selectBatchById(selectedBatch.batch_id);
      loadBatches(selectedBatch.batch_id);
    } catch (e) {
      console.error("Failed to apply batch:", e);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    if (!selectedBatch) return;
    setActionLoading(true);
    try {
      await pauseBatch(selectedBatch.batch_id);
      await selectBatchById(selectedBatch.batch_id);
    } catch (e) {
      console.error("Failed to pause batch:", e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!selectedBatch) return;
    setActionLoading(true);
    try {
      await resumeBatch(selectedBatch.batch_id);
      await selectBatchById(selectedBatch.batch_id);
    } catch (e) {
      console.error("Failed to resume batch:", e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!selectedBatch) return;
    setActionLoading(true);
    try {
      await stopBatch(selectedBatch.batch_id);
      await selectBatchById(selectedBatch.batch_id);
    } catch (e) {
      console.error("Failed to stop batch:", e);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-surface via-surface to-brand/10 border border-surfaceBorder p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium bg-brand/10 text-brand border border-brand/20">
            <Zap className="w-3.5 h-3.5" />
            PHASE 5 — BULK APPLICATION ENGINE
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            One-Click Multi-Job Discovery & Auto Apply
          </h1>
          <p className="text-sm text-gray-400 max-w-2xl leading-relaxed">
            Search worldwide vacancies, execute 12 automated preflight checks, synthesize role-specific tailored application packages, and submit authorized batch applications with a single confirmation.
          </p>
        </div>

        {/* Quick batch generation triggers */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-gray-400">Launch Preflight Batch:</span>
          <div className="flex items-center gap-2 flex-wrap">
            {[10, 25, 50].map((size) => (
              <button
                key={size}
                disabled={creatingSize !== null}
                onClick={() => handleCreateBatch(size)}
                className="px-3.5 py-2 rounded-xl bg-brand/10 hover:bg-brand/20 border border-brand/30 text-brand hover:text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm disabled:opacity-50"
              >
                {creatingSize === size ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>Top {size}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Batches Sidebar + Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Batches List (4 cols) */}
        <div className="lg:col-span-4 bg-surface border border-surfaceBorder rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand" />
              <h2 className="text-sm font-semibold text-white">Application Batches</h2>
            </div>
            <button
              onClick={() => loadBatches()}
              disabled={loading}
              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surfaceBorder/40 transition-colors"
              title="Refresh batches"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {batches.length === 0 && !loading && (
              <div className="p-8 text-center text-gray-500 text-xs">
                No application batches found. Click "Top 10" or "Top 25" above to preflight a new batch.
              </div>
            )}
            {batches.map((b) => {
              const isSelected = selectedBatch?.batch_id === b.batch_id;
              const isPreflight = b.status === "PREFLIGHTED";
              const isProcessing = b.status === "PROCESSING";
              const isCompleted = b.status === "COMPLETED";
              const isPaused = b.status === "PAUSED";

              return (
                <div
                  key={b.batch_id}
                  onClick={() => selectBatchById(b.batch_id)}
                  className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? "bg-brand/10 border-brand/40 shadow-sm"
                      : "bg-background/40 border-surfaceBorder hover:border-gray-600"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-gray-300 font-semibold truncate max-w-[170px]">
                      {b.name || b.batch_id}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider ${
                        isCompleted
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : isProcessing
                          ? "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"
                          : isPaused
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                      }`}
                    >
                      {b.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-gray-400">
                    <span>Target: {b.target_size} jobs</span>
                    <span>
                      {b.submitted_count || 0}/{b.eligible_jobs || 0} applied
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Batch Inspector (8 cols) */}
        <div className="lg:col-span-8 bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-6">
          {detailLoading ? (
            <div className="py-24 text-center text-gray-400 flex flex-col items-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-brand" />
              <p className="text-xs">Loading batch state & preflight audit...</p>
            </div>
          ) : !selectedBatch ? (
            <div className="py-24 text-center text-gray-500 text-xs">
              Select or generate a batch to view preflight breakdown and launch bulk applications.
            </div>
          ) : (
            <>
              {/* Batch Header & Action Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-surfaceBorder">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white font-mono">{selectedBatch.batch_id}</h2>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand/10 text-brand border border-brand/20">
                      {selectedBatch.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    Preflighted: {new Date(selectedBatch.created_at).toLocaleString()}
                  </p>
                </div>

                {/* State Control Buttons */}
                <div className="flex items-center gap-2">
                  {selectedBatch.status === "PREFLIGHTED" && (
                    <button
                      onClick={handleApplyBatch}
                      disabled={actionLoading || selectedBatch.eligible_jobs === 0}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand to-accent hover:opacity-95 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-brand/20 transition-all disabled:opacity-50"
                    >
                      {actionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                      <span>Authorize & Apply All ({selectedBatch.eligible_jobs})</span>
                    </button>
                  )}

                  {selectedBatch.status === "PROCESSING" && (
                    <button
                      onClick={handlePause}
                      disabled={actionLoading}
                      className="px-3.5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                    >
                      <Pause className="w-3.5 h-3.5" />
                      <span>Pause Batch</span>
                    </button>
                  )}

                  {selectedBatch.status === "PAUSED" && (
                    <button
                      onClick={handleResume}
                      disabled={actionLoading}
                      className="px-3.5 py-2 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Resume</span>
                    </button>
                  )}

                  {(selectedBatch.status === "PROCESSING" || selectedBatch.status === "PAUSED") && (
                    <button
                      onClick={handleStop}
                      disabled={actionLoading}
                      className="px-3 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-semibold flex items-center gap-1 transition-all"
                    >
                      <StopCircle className="w-3.5 h-3.5" />
                      <span>Stop</span>
                    </button>
                  )}

                  <button
                    onClick={() => selectBatchById(selectedBatch.batch_id)}
                    className="p-2 text-gray-400 hover:text-white rounded-xl hover:bg-surfaceBorder/40 transition-colors border border-surfaceBorder"
                    title="Refresh current batch"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-background/50 border border-surfaceBorder">
                  <div className="text-[11px] font-medium text-gray-400">Total Preflighted</div>
                  <div className="text-xl font-bold text-white mt-1">{selectedBatch.total_jobs}</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Top candidate jobs</div>
                </div>

                <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                  <div className="text-[11px] font-medium text-emerald-400">Direct API Submittable</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">
                    {selectedBatch.auto_submittable_jobs || 0}
                  </div>
                  <div className="text-[10px] text-emerald-500/70 mt-0.5">Greenhouse, Lever, Ashby</div>
                </div>

                <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20">
                  <div className="text-[11px] font-medium text-blue-400">Assisted Review Staged</div>
                  <div className="text-xl font-bold text-blue-400 mt-1">
                    {selectedBatch.manual_review_jobs || 0}
                  </div>
                  <div className="text-[10px] text-blue-500/70 mt-0.5">External career portals</div>
                </div>

                <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/20">
                  <div className="text-[11px] font-medium text-purple-400">Submitted & Receipted</div>
                  <div className="text-xl font-bold text-purple-400 mt-1">
                    {selectedBatch.submitted_count || 0}
                  </div>
                  <div className="text-[10px] text-purple-500/70 mt-0.5">Authoritative CONF IDs</div>
                </div>
              </div>

              {/* Batch Items List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Included Vacancies ({selectedBatch.items?.length || 0})
                  </h3>
                  <div className="flex items-center gap-2 text-[11px] text-gray-400">
                    <ShieldCheck className="w-3.5 h-3.5 text-brand" />
                    <span>Candidate: Mustkeem Ahmad</span>
                  </div>
                </div>

                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                  {(selectedBatch.items || []).map((item: any) => {
                    const isApiSubmitted = item.status === "SUBMITTED";
                    const isManualReview = item.status === "MANUAL_REVIEW_REQUIRED";
                    const isFailed = item.status === "FAILED";

                    return (
                      <div
                        key={item.id}
                        className="p-3.5 rounded-xl bg-background/40 border border-surfaceBorder hover:border-gray-700 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">{item.job_title}</span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-surface border border-surfaceBorder text-gray-300">
                              {item.company}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand/10 text-brand">
                              {item.match_score}% MATCH
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-[11px] text-gray-400">
                            <span>Capability: {item.capability}</span>
                            {item.confirmation_receipt_id && (
                              <span className="font-mono text-emerald-400 font-semibold">
                                Receipt: {item.confirmation_receipt_id}
                              </span>
                            )}
                            {item.exclusion_reason && (
                              <span className="text-amber-400">Reason: {item.exclusion_reason}</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span
                            className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                              isApiSubmitted
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : isManualReview
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                : isFailed
                                ? "bg-red-500/10 text-red-400 border border-red-500/20"
                                : "bg-gray-500/10 text-gray-400 border border-gray-500/20"
                            }`}
                          >
                            {item.status}
                          </span>

                          {item.application_url && (
                            <a
                              href={item.application_url}
                              target="_blank"
                              rel="noreferrer"
                              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surfaceBorder/40 transition-colors"
                              title="Open original job posting"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
