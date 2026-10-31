"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Briefcase, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  AlertCircle, 
  Sparkles, 
  ExternalLink,
  ChevronRight,
  ShieldAlert
} from "lucide-react";
import { fetchAnalyticsOverview, fetchApplications, fetchJobs } from "@/lib/api";

export default function OverviewPage() {
  const [stats, setStats] = useState<any>(null);
  const [pendingApps, setPendingApps] = useState<any[]>([]);
  const [topJobs, setTopJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [anData, appsData, jobsData] = await Promise.all([
          fetchAnalyticsOverview(),
          fetchApplications("AWAITING_APPROVAL"),
          fetchJobs({ min_score: 90 })
        ]);
        setStats(anData);
        setPendingApps(appsData.applications?.slice(0, 4) || []);
        setTopJobs(jobsData.jobs?.slice(0, 5) || []);
      } catch (err) {
        console.error("Error loading dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-surface via-surface to-brand/10 border border-surfaceBorder p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium bg-brand/10 text-brand border border-brand/20">
            <Sparkles className="w-3.5 h-3.5" />
            Autonomous AI Employment System
          </div>
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Welcome back, Mustkeem
          </h2>
          <p className="text-sm text-gray-400 max-w-2xl">
            Global Job Hunter is continuously crawling global employer ATS portals, matching your verified RLHF, LLM evaluation, and full-stack credentials, and preparing compliant applications.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/queue"
            className="px-4 py-2.5 rounded-xl bg-brand hover:bg-brandDark text-slate-950 font-semibold text-xs transition-all shadow-md flex items-center gap-2"
          >
            <Clock className="w-4 h-4" />
            <span>Review Queue ({stats?.awaiting_approval || 0})</span>
          </Link>
          <Link
            href="/jobs"
            className="px-4 py-2.5 rounded-xl bg-surface border border-surfaceBorder hover:border-gray-600 text-white font-medium text-xs transition-all"
          >
            Explore Jobs
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Jobs Discovered</span>
            <Briefcase className="w-4 h-4 text-brand" />
          </div>
          <div className="text-2xl font-bold text-white">{stats?.total_jobs_discovered || 0}</div>
          <div className="text-[11px] text-emerald-400">100% Verified live openings</div>
        </div>

        <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>High-Match Jobs</span>
            <Sparkles className="w-4 h-4 text-accent" />
          </div>
          <div className="text-2xl font-bold text-white">{stats?.high_match_jobs || 0}</div>
          <div className="text-[11px] text-accent">Score ≥ 85/100 compatibility</div>
        </div>

        <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Awaiting Approval</span>
            <Clock className="w-4 h-4 text-warning" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{stats?.awaiting_approval || 0}</div>
          <div className="text-[11px] text-gray-400">Mode B: Ready for review</div>
        </div>

        <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Applications Submitted</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">{stats?.submitted_confirmed || 0}</div>
          <div className="text-[11px] text-emerald-400/80">With confirmed receipts</div>
        </div>
      </div>

      {/* Two Column Layout: Pending Approvals & Top Verified Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Queue Card */}
        <div className="rounded-2xl bg-surface border border-surfaceBorder p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-warning" />
              <h3 className="font-semibold text-sm text-white">Pending Approval Queue</h3>
            </div>
            <Link href="/queue" className="text-xs text-brand hover:underline flex items-center gap-1">
              View all <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {pendingApps.length === 0 ? (
            <div className="py-10 text-center text-gray-400 text-xs space-y-2 border border-dashed border-surfaceBorder rounded-xl">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
              <p>No applications waiting in queue.</p>
              <p className="text-[11px] text-gray-500">Go to Job Explorer and click "Prepare Application" on any role.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingApps.map((app) => (
                <div
                  key={app.id}
                  className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder hover:border-surfaceBorder/80 transition-all flex items-center justify-between gap-4"
                >
                  <div className="space-y-1 min-w-0">
                    <h4 className="font-medium text-xs text-white truncate">{app.title}</h4>
                    <p className="text-[11px] text-gray-400">{app.company_name} • {app.compensation}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-brand/10 text-brand border border-brand/30">
                      {app.match_score}/100
                    </span>
                    <Link
                      href="/queue"
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20"
                    >
                      Review
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Highest Match Verified Openings */}
        <div className="rounded-2xl bg-surface border border-surfaceBorder p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent" />
              <h3 className="font-semibold text-sm text-white">Top 90+ Match Opportunities</h3>
            </div>
            <Link href="/jobs" className="text-xs text-brand hover:underline flex items-center gap-1">
              Browse all <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {topJobs.map((job) => (
              <div
                key={job.id}
                className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder hover:border-brand/40 transition-all flex items-center justify-between gap-4"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-xs text-white truncate">{job.title}</h4>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-accent/20 text-accent">
                      {job.match_score}/100
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-400">
                    {job.company_name} • <span className="text-emerald-400 font-mono">{job.compensation_text}</span>
                  </p>
                </div>
                <a
                  href={job.application_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 rounded-md text-xs font-medium text-gray-400 hover:text-white border border-surfaceBorder hover:border-gray-500 flex items-center gap-1 shrink-0"
                >
                  <span>Portal</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
