"use client";
import React, { useEffect, useState } from "react";
import { BarChart3, TrendingUp, Briefcase, CheckCircle2, DollarSign, Loader2 } from "lucide-react";
import { fetchAnalyticsOverview } from "@/lib/api";

export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchAnalyticsOverview();
        setStats(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">System Performance & Pipeline Analytics</h2>
        <p className="text-xs text-gray-400">
          Conversion funnels, compensation distributions, and crawl performance across global sources.
        </p>
      </div>

      {loading ? (
        <div className="py-20 text-center text-gray-400 text-xs">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
          Loading analytics...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Funnel Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-1">
              <span className="text-xs text-gray-400">Total Crawled</span>
              <div className="text-2xl font-bold text-white">{stats?.total_jobs_discovered || 0}</div>
              <span className="text-[10px] text-gray-500 font-mono">100% deduplicated</span>
            </div>
            <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-1">
              <span className="text-xs text-gray-400">Match Qualified (≥85)</span>
              <div className="text-2xl font-bold text-brand">{stats?.high_match_jobs || 0}</div>
              <span className="text-[10px] text-brand/80 font-mono">High suitability</span>
            </div>
            <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-1">
              <span className="text-xs text-gray-400">Total Applications</span>
              <div className="text-2xl font-bold text-accent">{stats?.total_applications || 0}</div>
              <span className="text-[10px] text-accent/80 font-mono">Prepared & Staged</span>
            </div>
            <div className="p-5 rounded-xl bg-surface border border-surfaceBorder space-y-1">
              <span className="text-xs text-gray-400">Verified Submissions</span>
              <div className="text-2xl font-bold text-emerald-400">{stats?.submitted_confirmed || 0}</div>
              <span className="text-[10px] text-emerald-400/80 font-mono">With confirmation ID</span>
            </div>
          </div>

          {/* Compensation & Track Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
              <h3 className="font-semibold text-xs text-white uppercase tracking-wider">
                Earning Bands by Opportunity Track
              </h3>
              <div className="space-y-3 text-xs">
                <div className="space-y-1">
                  <div className="flex justify-between text-gray-300">
                    <span>AI Training & RLHF (Surge AI, Alignerr, Mercor)</span>
                    <strong className="text-brand font-mono">$45 – $150 / hr</strong>
                  </div>
                  <div className="h-2 rounded-full bg-background overflow-hidden">
                    <div className="h-full bg-brand rounded-full w-[95%]" />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-gray-300">
                    <span>Full-Stack Engineering (HTTPie, Anyone AI, Bloomreach)</span>
                    <strong className="text-emerald-400 font-mono">$60k – $115k / yr</strong>
                  </div>
                  <div className="h-2 rounded-full bg-background overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full w-[80%]" />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-gray-300">
                    <span>Global Freelance (Contra, Braintrust, Upwork)</span>
                    <strong className="text-accent font-mono">$35 – $95 / hr</strong>
                  </div>
                  <div className="h-2 rounded-full bg-background overflow-hidden">
                    <div className="h-full bg-accent rounded-full w-[75%]" />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-gray-300">
                    <span>AI Evaluation & QA (TELUS, OneForma, Mindrift)</span>
                    <strong className="text-amber-400 font-mono">$15 – $40 / hr</strong>
                  </div>
                  <div className="h-2 rounded-full bg-background overflow-hidden">
                    <div className="h-full bg-amber-400 rounded-full w-[45%]" />
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
              <h3 className="font-semibold text-xs text-white uppercase tracking-wider">
                Country Eligibility Distribution
              </h3>
              <div className="space-y-3 text-xs">
                <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder flex items-center justify-between">
                  <span className="text-white">Confirmed India Eligible & Worldwide</span>
                  <span className="font-bold text-emerald-400 font-mono">100% of tracked pool</span>
                </div>
                <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder flex items-center justify-between">
                  <span className="text-white">Contract Model (B2B / 1099)</span>
                  <span className="font-bold text-brand font-mono">Supported & Verified</span>
                </div>
                <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder flex items-center justify-between">
                  <span className="text-white">Remote Employment (EOR / Deel)</span>
                  <span className="font-bold text-accent font-mono">Supported</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
