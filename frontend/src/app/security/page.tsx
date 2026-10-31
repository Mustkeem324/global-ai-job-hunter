"use client";
import React, { useEffect, useState } from "react";
import { ShieldCheck, Lock, AlertTriangle, FileCode, CheckCircle2, Loader2 } from "lucide-react";
import { fetchAuditLogs } from "@/lib/api";

export default function SecurityPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchAuditLogs();
        setLogs(data.events || []);
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
        <h2 className="text-xl font-bold text-white tracking-tight">Security Controls & Audit Log</h2>
        <p className="text-xs text-gray-400">
          Strict least-privilege security safeguards, prompt-injection defense mechanisms, and state transition audit trails.
        </p>
      </div>

      {/* Security Health Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-surface border border-surfaceBorder space-y-1">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4" />
            <span>SSRF & URL Whitelisting</span>
          </div>
          <p className="text-[11px] text-gray-400">
            Blocks private/loopback IP address routing for external application endpoints.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surfaceBorder space-y-1">
          <div className="flex items-center gap-2 text-brand text-xs font-semibold">
            <Lock className="w-4 h-4" />
            <span>Prompt Injection Neutralizer</span>
          </div>
          <p className="text-[11px] text-gray-400">
            Sanitizes adversarial instructions embedded within untrusted external job postings.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surfaceBorder space-y-1">
          <div className="flex items-center gap-2 text-accent text-xs font-semibold">
            <FileCode className="w-4 h-4" />
            <span>Authoritative Evidence Required</span>
          </div>
          <p className="text-[11px] text-gray-400">
            Applications cannot be marked confirmed without verifiable receipts or API confirmation IDs.
          </p>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-xl bg-surface border border-surfaceBorder overflow-hidden">
        <div className="p-4 border-b border-surfaceBorder font-semibold text-xs text-white">
          State Machine Transition Audit Trail
        </div>

        {loading ? (
          <div className="py-16 text-center text-gray-400 text-xs">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
            Loading audit events...
          </div>
        ) : logs.length === 0 ? (
          <div className="py-16 text-center text-gray-400 text-xs">
            No state machine audit events recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-surfaceBorder bg-background/50 text-gray-400 text-[11px] uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Event ID</th>
                  <th className="py-3 px-4">Transition</th>
                  <th className="py-3 px-4">Trigger</th>
                  <th className="py-3 px-4">Details</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surfaceBorder">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-surfaceBorder/20 transition-all font-mono text-[11px]">
                    <td className="py-3 px-4 text-gray-400">#{log.id}</td>
                    <td className="py-3 px-4 text-brand">
                      {log.from_status} → <strong className="text-white">{log.to_status}</strong>
                    </td>
                    <td className="py-3 px-4 text-emerald-400">{log.trigger}</td>
                    <td className="py-3 px-4 text-gray-300 font-sans text-xs">{log.message}</td>
                    <td className="py-3 px-4 text-gray-400">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
