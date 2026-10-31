"use client";
import React, { useEffect, useState } from "react";
import { Clock, CheckCircle2, XCircle, ArrowUpRight, FileText, Send, Loader2 } from "lucide-react";
import { fetchApplications, fetchApplicationDetail, approveApplication, rejectApplication, markAssistedSubmitted } from "@/lib/api";

export default function QueuePage() {
  const [apps, setApps] = useState<any[]>([]);
  const [selectedApp, setSelectedApp] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [assistedNotes, setAssistedNotes] = useState("");

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await fetchApplications();
      // Filter for actionable applications
      const actionable = (data.applications || []).filter(
        (a: any) => a.status === "AWAITING_APPROVAL" || a.status === "PREPARED"
      );
      setApps(actionable);
      if (actionable.length > 0) {
        const detail = await fetchApplicationDetail(actionable[0].id);
        setSelectedApp(detail);
      } else {
        setSelectedApp(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleSelect = async (appId: number) => {
    try {
      const detail = await fetchApplicationDetail(appId);
      setSelectedApp(detail);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApprove = async () => {
    if (!selectedApp) return;
    setActionLoading(true);
    try {
      await approveApplication(selectedApp.id);
      await loadQueue();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedApp) return;
    setActionLoading(true);
    try {
      await rejectApplication(selectedApp.id, "Candidate opted not to proceed");
      await loadQueue();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkAssisted = async () => {
    if (!selectedApp) return;
    setActionLoading(true);
    try {
      await markAssistedSubmitted(selectedApp.id, assistedNotes || "Completed via employer portal");
      setAssistedNotes("");
      await loadQueue();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Application Approval Queue</h2>
        <p className="text-xs text-gray-400">
          Mode B & Mode C applications staged for review. Examine tailored documents before authorizing submission.
        </p>
      </div>

      {loading ? (
        <div className="py-20 text-center text-gray-400 text-xs">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
          Loading approval queue...
        </div>
      ) : apps.length === 0 ? (
        <div className="py-20 text-center text-gray-400 text-xs border border-dashed border-surfaceBorder rounded-xl space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
          <p className="font-medium text-white">Your approval queue is clear!</p>
          <p className="text-[11px] text-gray-500">
            Head to the Job Explorer to stage tailored applications for high-match positions.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Application Cards List */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Staged Applications ({apps.length})
            </span>
            {apps.map((app) => {
              const isSelected = selectedApp?.id === app.id;
              return (
                <div
                  key={app.id}
                  onClick={() => handleSelect(app.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-surface border-brand shadow-md shadow-brand/10"
                      : "bg-surface/50 border-surfaceBorder hover:border-gray-600"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-semibold uppercase text-gray-400">
                      {app.company_name}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-brand/10 text-brand">
                      {app.match_score}/100
                    </span>
                  </div>
                  <h4 className="font-semibold text-xs text-white mt-1 truncate">{app.title}</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5">{app.compensation}</p>
                </div>
              );
            })}
          </div>

          {/* Right Column: Active Application Review Pane */}
          {selectedApp && (
            <div className="lg:col-span-2 space-y-6 bg-surface border border-surfaceBorder p-6 rounded-2xl">
              <div className="flex items-start justify-between gap-4 border-b border-surfaceBorder pb-4">
                <div>
                  <span className="text-xs font-medium text-brand">{selectedApp.job.company_name}</span>
                  <h3 className="text-lg font-bold text-white">{selectedApp.job.title}</h3>
                  <p className="text-xs text-gray-400">{selectedApp.job.location} • {selectedApp.job.compensation}</p>
                </div>
                <a
                  href={selectedApp.job.application_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-300 hover:text-white border border-surfaceBorder hover:border-gray-500 flex items-center gap-1.5 shrink-0"
                >
                  <span>Portal</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </a>
              </div>

              {/* Tailored Professional Headline & Summary */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                  Tailored Professional Summary
                </h4>
                <div className="p-3.5 rounded-xl bg-background/70 border border-surfaceBorder text-xs text-gray-300 leading-relaxed font-mono">
                  {selectedApp.tailored_summary}
                </div>
              </div>

              {/* Personalized Cover Letter */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Generated Cover Letter
                  </h4>
                  <span className="text-[11px] text-gray-500">Factual evidence substantiated</span>
                </div>
                <textarea
                  readOnly
                  rows={8}
                  value={selectedApp.cover_letter}
                  className="w-full p-3.5 rounded-xl bg-background/70 border border-surfaceBorder text-xs text-gray-300 font-mono leading-relaxed resize-none focus:outline-none"
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-surfaceBorder flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <button
                    onClick={handleApprove}
                    disabled={actionLoading}
                    className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 flex items-center justify-center gap-1.5 transition-all shadow-md"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve & Authorize Submission</span>
                  </button>

                  <button
                    onClick={handleReject}
                    disabled={actionLoading}
                    className="px-3 py-2 rounded-xl text-xs font-semibold bg-surface border border-surfaceBorder hover:border-red-500/50 text-red-400 flex items-center gap-1.5 transition-all"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                </div>

                {/* Assisted Mode Quick Confirm */}
                <div className="w-full sm:w-auto flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Confirmation receipt note..."
                    value={assistedNotes}
                    onChange={(e) => setAssistedNotes(e.target.value)}
                    className="px-3 py-1.5 rounded-lg bg-background border border-surfaceBorder text-xs text-white placeholder-gray-500 w-44"
                  />
                  <button
                    onClick={handleMarkAssisted}
                    disabled={actionLoading}
                    className="px-3 py-2 rounded-xl text-xs font-medium bg-brand/10 text-brand border border-brand/30 hover:bg-brand/20 whitespace-nowrap"
                  >
                    Mark Assisted Done
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
