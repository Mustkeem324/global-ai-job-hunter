"use client";
import React, { useEffect, useState } from "react";
import { CheckCircle2, ExternalLink, ShieldCheck, Clock, AlertTriangle, Loader2 } from "lucide-react";
import { fetchApplications } from "@/lib/api";

export default function HistoryPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchApplications();
        setApps(data.applications || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Application History & Audit Records</h2>
        <p className="text-xs text-gray-400">
          Immutable audit timeline of all processed applications with verified submission receipts and confirmation IDs.
        </p>
      </div>

      {loading ? (
        <div className="py-20 text-center text-gray-400 text-xs">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
          Loading audit records...
        </div>
      ) : apps.length === 0 ? (
        <div className="py-20 text-center text-gray-400 text-xs border border-dashed border-surfaceBorder rounded-xl">
          No application records logged yet.
        </div>
      ) : (
        <div className="rounded-xl bg-surface border border-surfaceBorder overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-surfaceBorder bg-background/50 text-gray-400 text-[11px] uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Company & Position</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Match</th>
                  <th className="py-3 px-4">Evidence / Confirmation ID</th>
                  <th className="py-3 px-4">Date Applied</th>
                  <th className="py-3 px-4 text-right">Portal Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surfaceBorder">
                {apps.map((app) => {
                  const isConfirmed = app.status === "SUBMITTED_CONFIRMED";
                  const isAwaiting = app.status === "AWAITING_APPROVAL";
                  const isRejected = app.status === "REJECTED";

                  return (
                    <tr key={app.id} className="hover:bg-surfaceBorder/20 transition-all">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white">{app.title}</div>
                        <div className="text-[11px] text-gray-400">{app.company_name}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${
                            isConfirmed
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : isAwaiting
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : isRejected
                              ? "bg-red-500/10 text-red-400 border-red-500/20"
                              : "bg-surfaceBorder text-gray-300 border-gray-700"
                          }`}
                        >
                          {isConfirmed ? (
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          ) : isAwaiting ? (
                            <Clock className="w-3 h-3 text-amber-400" />
                          ) : (
                            <ShieldCheck className="w-3 h-3 text-gray-400" />
                          )}
                          <span>{app.status}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-bold text-brand">{app.match_score}/100</td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-gray-300">
                        {app.confirmation_id ? (
                          <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            {app.confirmation_id}
                          </span>
                        ) : (
                          <span className="text-gray-500 italic">Pending submission</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-gray-400">
                        {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <a
                          href={app.application_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-gray-400 hover:text-white"
                        >
                          <span>Portal</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
