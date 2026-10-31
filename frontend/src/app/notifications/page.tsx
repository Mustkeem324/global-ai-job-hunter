"use client";
import React, { useEffect, useState } from "react";
import { Bell, Send, CheckCircle2, AlertCircle, Sparkles, Loader2 } from "lucide-react";
import { fetchTelegramStatus, sendTelegramTest } from "@/lib/api";

export default function NotificationsPage() {
  const [status, setStatus] = useState<any>(null);
  const [testMsg, setTestMsg] = useState("🚀 Testing Global Job Hunter Telegram notification webhook.");
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchTelegramStatus();
        setStatus(data);
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, []);

  const handleSendTest = async () => {
    setSending(true);
    setSendResult(null);
    try {
      const res = await sendTelegramTest(testMsg);
      setSendResult(res);
    } catch (e) {
      setSendResult({ success: false, error: String(e) });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Notification Channels</h2>
        <p className="text-xs text-gray-400">
          Real-time Telegram Bot API alerts for high-match opportunities, approval requests, and verified application receipts.
        </p>
      </div>

      <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-6">
        <div className="flex items-center justify-between border-b border-surfaceBorder pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#229ED9]/10 border border-[#229ED9]/30 flex items-center justify-center text-[#229ED9]">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-white">Telegram Bot API</h3>
              <p className="text-xs text-gray-400 font-mono">
                {status?.is_configured ? `Active • Chat ID: ${status.chat_id}` : "Ready for Bot Token Configuration"}
              </p>
            </div>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-medium border ${
              status?.is_configured
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }`}
          >
            {status?.is_configured ? "Configured" : "Simulation Mode (Local)"}
          </span>
        </div>

        {/* Test Alert Sender */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-gray-300">Dispatch Test Alert</label>
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={testMsg}
              onChange={(e) => setTestMsg(e.target.value)}
              className="flex-1 px-3.5 py-2 rounded-xl bg-background border border-surfaceBorder text-xs text-white focus:outline-none focus:border-brand"
            />
            <button
              onClick={handleSendTest}
              disabled={sending}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#229ED9] hover:bg-[#1f8ec4] text-white flex items-center gap-2 shrink-0 transition-all shadow-md"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>Send Test</span>
            </button>
          </div>
        </div>

        {/* Send Result */}
        {sendResult && (
          <div className="p-4 rounded-xl bg-background border border-surfaceBorder space-y-2">
            <div className="flex items-center gap-2 text-xs">
              {sendResult.success ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 font-medium">Notification triggered successfully!</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <span className="text-red-400 font-medium">Error sending notification</span>
                </>
              )}
            </div>
            <pre className="text-[11px] text-gray-400 font-mono overflow-x-auto bg-surface p-3 rounded-lg border border-surfaceBorder">
              {JSON.stringify(sendResult, null, 2)}
            </pre>
          </div>
        )}

        {/* Event Triggers List */}
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Automated Alert Event Triggers
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
              <span className="font-semibold text-white">🚀 New High-Match Opportunity</span>
              <p className="text-[11px] text-gray-400">Triggered whenever a discovered job scores ≥ 90/100 compatibility.</p>
            </div>
            <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
              <span className="font-semibold text-white">📋 Application Ready for Approval</span>
              <p className="text-[11px] text-gray-400">Sent when tailored documents and answers are ready for your review.</p>
            </div>
            <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
              <span className="font-semibold text-white">✅ Application Confirmed</span>
              <p className="text-[11px] text-gray-400">Delivered immediately upon authoritative receipt with Confirmation ID.</p>
            </div>
            <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
              <span className="font-semibold text-white">📊 Daily 9:00 AM Search Digest</span>
              <p className="text-[11px] text-gray-400">Morning summary of crawling metrics and active pipeline counts.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
