"use client";
import React, { useEffect, useState } from "react";
import { 
  Users, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Sparkles, 
  Send, 
  ExternalLink, 
  RefreshCw,
  TrendingUp,
  Brain,
  Shield,
  MessageSquare,
  FileCheck
} from "lucide-react";
import { 
  fetchRecruiterPipeline, 
  fetchRecruiterContacts, 
  fetchFollowups, 
  generateFollowupDraft, 
  approveFollowupDraft, 
  rejectFollowupDraft, 
  snoozeFollowupDraft, 
  fetchInterviews, 
  syncInterviewCalendar, 
  fetchInterviewPrep, 
  fetchTargetingRecommendations 
} from "@/lib/api";

export default function PipelinePage() {
  const [activeTab, setActiveTab] = useState<"funnel" | "interviews" | "followups" | "recruiters" | "recommendations">("funnel");
  const [loading, setLoading] = useState(true);
  const [pipelineData, setPipelineData] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [followups, setFollowups] = useState<any[]>([]);
  const [interviews, setInterviews] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [prepModalData, setPrepModalData] = useState<any>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [pipe, cnt, fup, intv, recs] = await Promise.all([
        fetchRecruiterPipeline(),
        fetchRecruiterContacts(),
        fetchFollowups(),
        fetchInterviews(),
        fetchTargetingRecommendations()
      ]);
      setPipelineData(pipe);
      setContacts(cnt.contacts || []);
      setFollowups(fup.recommendations || []);
      setInterviews(intv.interviews || []);
      setRecommendations(recs.recommendations || []);
    } catch (err) {
      console.error("Failed to load pipeline data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleApproveFollowup = async (draftId: number) => {
    setActionLoading(true);
    try {
      await approveFollowupDraft(draftId, { approved_by: "web_admin" });
      await loadAllData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectFollowup = async (draftId: number) => {
    setActionLoading(true);
    try {
      await rejectFollowupDraft(draftId, "Dismissed via Web Dashboard");
      await loadAllData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSnoozeFollowup = async (draftId: number) => {
    setActionLoading(true);
    try {
      await snoozeFollowupDraft(draftId, 5);
      await loadAllData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSyncCalendar = async (intvId: number) => {
    setActionLoading(true);
    try {
      await syncInterviewCalendar(intvId);
      await loadAllData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenPrep = async (applicationId: number) => {
    try {
      const prep = await fetchInterviewPrep(applicationId);
      setPrepModalData(prep);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-8">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-surface via-surface to-brand/10 border border-surfaceBorder p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium bg-brand/10 text-brand border border-brand/20">
            <Sparkles className="w-3.5 h-3.5" />
            PHASE 6 — RECRUITER & APPLICATION CONVERSION SYSTEM
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Recruiter Intelligence & Interview Management
          </h1>
          <p className="text-sm text-gray-400 max-w-2xl leading-relaxed">
            Monitor employer correspondence, manage upcoming interviews in Asia/Kolkata timezone, approve evidence-based follow-ups, and track end-to-end recruitment funnel conversions.
          </p>
        </div>

        <button
          onClick={loadAllData}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-surface border border-surfaceBorder hover:border-gray-500 text-gray-300 hover:text-white text-xs font-semibold flex items-center gap-2 transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Pipeline</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-surfaceBorder pb-3 overflow-x-auto text-xs font-medium">
        {[
          { key: "funnel", label: "Application Funnel & Rates", icon: TrendingUp },
          { key: "interviews", label: `Interviews (${interviews.length})`, icon: Calendar },
          { key: "followups", label: `Follow-Up Queue (${followups.length})`, icon: Clock },
          { key: "recruiters", label: `Recruiter CRM (${contacts.length})`, icon: Users },
          { key: "recommendations", label: `AI Targeting Suggestions (${recommendations.length})`, icon: Brain }
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

      {/* TAB 1: FUNNEL */}
      {activeTab === "funnel" && pipelineData && (
        <div className="space-y-6">
          {/* Key Rates Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder shadow-sm space-y-2">
              <span className="text-xs font-medium text-gray-400">Employer Response Rate</span>
              <div className="text-3xl font-bold text-white font-mono">
                {pipelineData.rates?.response_rate?.percentage}%
              </div>
              <div className="text-[11px] text-gray-500">
                {pipelineData.rates?.response_rate?.numerator} responses / {pipelineData.rates?.response_rate?.denominator} confirmed submissions
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder shadow-sm space-y-2">
              <span className="text-xs font-medium text-emerald-400">Interview Rate</span>
              <div className="text-3xl font-bold text-emerald-400 font-mono">
                {pipelineData.rates?.interview_rate?.percentage}%
              </div>
              <div className="text-[11px] text-emerald-500/70">
                {pipelineData.rates?.interview_rate?.numerator} interviews / {pipelineData.rates?.interview_rate?.denominator} confirmed submissions
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder shadow-sm space-y-2">
              <span className="text-xs font-medium text-purple-400">Offer Rate</span>
              <div className="text-3xl font-bold text-purple-400 font-mono">
                {pipelineData.rates?.offer_rate?.percentage}%
              </div>
              <div className="text-[11px] text-purple-500/70">
                {pipelineData.rates?.offer_rate?.numerator} offers / {pipelineData.rates?.offer_rate?.denominator} confirmed submissions
              </div>
            </div>
          </div>

          {/* Funnel Stages */}
          <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
            <h3 className="text-sm font-semibold text-white">Full Application Stage Breakdown</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {[
                { label: "Submitted", val: pipelineData.confirmed_submitted, color: "text-blue-400" },
                { label: "Acknowledged", val: pipelineData.employer_acknowledgments, color: "text-gray-300" },
                { label: "Under Review", val: pipelineData.under_review, color: "text-amber-400" },
                { label: "Assessments", val: pipelineData.assessments_invited, color: "text-cyan-400" },
                { label: "Interviews", val: pipelineData.interviews_invited, color: "text-emerald-400" },
                { label: "Offers", val: pipelineData.offers_received, color: "text-purple-400" }
              ].map((stage) => (
                <div key={stage.label} className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder text-center">
                  <div className={`text-xl font-bold ${stage.color} font-mono`}>{stage.val}</div>
                  <div className="text-[11px] text-gray-400 mt-1">{stage.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Role Category Breakdown */}
          {pipelineData.category_breakdown && (
            <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
              <h3 className="text-sm font-semibold text-white">Conversion Performance by Role Category</h3>
              <div className="space-y-2">
                {pipelineData.category_breakdown.map((cat: any) => (
                  <div key={cat.category} className="p-3.5 rounded-xl bg-background/40 border border-surfaceBorder flex items-center justify-between text-xs">
                    <div>
                      <div className="font-semibold text-white">{cat.category}</div>
                      <div className="text-[11px] text-gray-400">{cat.applications} applications submitted</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-emerald-400 font-semibold">{cat.interview_rate}% INTERVIEW RATE</div>
                      <div className="text-[11px] text-gray-500">{cat.interviews} interviews secured</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: INTERVIEWS */}
      {activeTab === "interviews" && (
        <div className="space-y-4">
          {interviews.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-xs bg-surface border border-surfaceBorder rounded-2xl">
              No upcoming interviews scheduled yet. When recruiter invitations arrive via Gmail, they will appear here automatically.
            </div>
          ) : (
            interviews.map((iv) => (
              <div key={iv.id} className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-3">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold text-white">{iv.title}</h3>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Recruiter: {iv.interviewer || "Hiring Team"} • Platform: <b>{iv.platform}</b>
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 self-start md:self-auto">
                    {iv.status}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-background/60 border border-surfaceBorder flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 text-gray-300">
                    <Clock className="w-4 h-4 text-brand" />
                    <span><b>Time (Asia/Kolkata):</b> {iv.scheduled_kolkata}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {iv.meeting_url && (
                      <a
                        href={iv.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-surfaceBorder/60 hover:bg-surfaceBorder text-gray-200 text-xs font-medium flex items-center gap-1.5 transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Open Meeting</span>
                      </a>
                    )}
                    <button
                      onClick={() => handleSyncCalendar(iv.id)}
                      disabled={actionLoading || iv.calendar_synced}
                      className="px-3 py-1.5 rounded-lg bg-brand/10 hover:bg-brand/20 text-brand text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{iv.calendar_synced ? "Calendar Synced" : "Sync Calendar"}</span>
                    </button>
                    <button
                      onClick={() => handleOpenPrep(iv.application_id)}
                      className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand to-accent text-white text-xs font-bold flex items-center gap-1.5 shadow-sm"
                    >
                      <Brain className="w-3.5 h-3.5" />
                      <span>AI Prep</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 3: FOLLOW-UPS */}
      {activeTab === "followups" && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs flex items-center gap-2">
            <Shield className="w-4 h-4 shrink-0" />
            <span>Strict Human-in-the-Loop Policy: Global Job Hunter AI never automatically sends unsolicited follow-ups. Every message requires your explicit approval.</span>
          </div>

          {followups.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-xs bg-surface border border-surfaceBorder rounded-2xl">
              All applications are currently up to date. No follow-ups pending review.
            </div>
          ) : (
            followups.map((f) => (
              <div key={f.recommendation_id} className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-3">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-white">{f.company} — {f.title}</h3>
                    <p className="text-xs text-gray-400 mt-0.5">{f.reason}</p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-brand/10 text-brand border border-brand/20 self-start md:self-auto">
                    {f.type}
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-surfaceBorder">
                  <button
                    onClick={() => handleApproveFollowup(f.recommendation_id)}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve & Log Sent</span>
                  </button>
                  <button
                    onClick={() => handleSnoozeFollowup(f.recommendation_id)}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>Snooze 5 Days</span>
                  </button>
                  <button
                    onClick={() => handleRejectFollowup(f.recommendation_id)}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-semibold flex items-center gap-1 transition-all"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Dismiss</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 4: RECRUITER CRM */}
      {activeTab === "recruiters" && (
        <div className="space-y-3">
          {contacts.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-xs bg-surface border border-surfaceBorder rounded-2xl">
              No recruiter contacts logged yet. Verified contacts are automatically recorded from incoming recruiter correspondence.
            </div>
          ) : (
            contacts.map((c) => (
              <div key={c.id} className="p-4 rounded-xl bg-surface border border-surfaceBorder flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                <div>
                  <div className="font-semibold text-white text-sm">{c.contact_name}</div>
                  <div className="text-gray-400 mt-0.5">
                    {c.company} • {c.job_position || "Recruiter"}
                  </div>
                  <div className="font-mono text-gray-500 text-[11px] mt-1">
                    Email: {c.email} {c.is_no_reply && <span className="text-red-400">(No-Reply)</span>}
                  </div>
                </div>
                <div className="text-right">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-brand/10 text-brand">
                    {c.follow_up_status}
                  </span>
                  <div className="text-[10px] text-gray-500 mt-1">
                    {c.interaction_count} logged interactions
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 5: AI RECOMMENDATIONS */}
      {activeTab === "recommendations" && (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div key={rec.id} className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-2">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-brand" />
                <h3 className="text-sm font-bold text-white">{rec.title}</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {int(rec.confidence * 100)}% Confidence
                </span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">{rec.observation}</p>
              <div className="p-3 rounded-xl bg-background/50 border border-surfaceBorder text-xs text-brand mt-2">
                <b>Actionable Directive:</b> {rec.actionable_suggestion}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PREPARATION MODAL */}
      {prepModalData && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-surfaceBorder rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-surfaceBorder pb-4">
              <div>
                <h2 className="text-base font-bold text-white">AI Interview Preparation</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  {prepModalData.role} at {prepModalData.company}
                </p>
              </div>
              <button
                onClick={() => setPrepModalData(null)}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surfaceBorder"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Candidate Grounded Credentials */}
            <div className="p-4 rounded-xl bg-background/50 border border-surfaceBorder space-y-2 text-xs">
              <span className="font-semibold text-gray-300">Grounded Credentials (Mustkeem Ahmad):</span>
              <ul className="list-disc list-inside text-gray-400 space-y-1">
                {prepModalData.grounded_credentials?.map((c: string, idx: number) => (
                  <li key={idx}>{c}</li>
                ))}
              </ul>
            </div>

            {/* Key Focus Areas */}
            <div className="space-y-2 text-xs">
              <span className="font-semibold text-white">Technical Focus Areas:</span>
              <ul className="space-y-2">
                {prepModalData.prep_content?.key_focus_areas?.map((fa: string, idx: number) => (
                  <li key={idx} className="p-3 rounded-xl bg-background/40 border border-surfaceBorder text-gray-300">
                    {fa}
                  </li>
                ))}
              </ul>
            </div>

            {/* Sample QA */}
            {prepModalData.prep_content?.sample_questions_and_grounded_answers && (
              <div className="space-y-3 text-xs">
                <span className="font-semibold text-white">Practice Questions & Grounded Answers:</span>
                {prepModalData.prep_content.sample_questions_and_grounded_answers.map((qa: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl bg-background/60 border border-surfaceBorder space-y-2">
                    <div className="font-semibold text-brand">Q: {qa.question}</div>
                    <div className="text-gray-300 leading-relaxed italic bg-surface/50 p-3 rounded-lg border border-surfaceBorder/60">
                      Suggested Answer: {qa.suggested_answer}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function int(val: number) {
  return Math.round(val);
}
