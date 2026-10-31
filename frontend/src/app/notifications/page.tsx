"use client";
import React, { useEffect, useState } from "react";
import { 
  Bell, 
  Send, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  Loader2, 
  Bot, 
  Terminal, 
  Copy, 
  Check 
} from "lucide-react";
import { fetchTelegramStatus, sendTelegramTest } from "@/lib/api";

export default function NotificationsPage() {
  const [status, setStatus] = useState<any>(null);
  const [testMsg, setTestMsg] = useState("🚀 Testing Global Job Hunter Telegram notification webhook.");
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const startMessagePreview = `💎 GLOBAL JOB HUNTER AI — PREMIER AUTONOMOUS CAREER SUITE
Elite Engineering & AI Career Orchestration Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👑 WELCOME TO YOUR PRIVATE AI RECRUITMENT AGENT
This is not a generic job-scraper or spam bot. You are connected to a high-end, self-hosted autonomous AI agent engineered specifically to hunt, verify, and land premium international employment ($40–$150/hr | $75,000–$150,000/yr) across:

• Frontier AI Training & RLHF (Surge AI, Alignerr, Mercor, Outlier, Handshake)
• Full-Stack & Systems Architecture (Python, Django, FastAPI, React, Next.js)
• Autonomous AI Agents & Automation Pipelines
• Global Independent Contractor Engagements (Contra, Braintrust, Lemon.io)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ HOW THE SYSTEM WORKS (IN-DEPTH ARCHITECTURE):

1️⃣ Autonomous Multi-Source Discovery:
Every 6 hours, our modular connectors monitor official ATS endpoints (Greenhouse, Lever, Ashby), global remote APIs (Remotive), and premier AI training platforms. All opportunities are deduplicated and verified active.

2️⃣ 6-Pillar Neural Match Engine (0–100 Heuristic):
Each vacancy is rigorously evaluated against your verified resume credentials:
• Technical Skills Match: 30%
• Demonstrable Professional Experience: 20%
• India Remote & Work Authorization Eligibility: 20%
• Educational Qualifications: 10%
• Role Preferences: 10%
• Opportunity Recency & Quality: 10%
(Vacancies scoring under 80/100 are automatically rejected or flagged.)

3️⃣ Fact-Substantiated Document Synthesis:
Our AI generator creates tailored professional summaries, custom cover letters, and standard question answers using strictly substantiated facts from your background (UPES MBA CGPA 8.90, Jamia B.Tech 83.3%, 200+ FreelanceKar deliveries, Handshake Dynamo, Outlier AI). Zero hallucinations or fabricated skills.

4️⃣ 3 Application Execution Modes:
• Mode A (Autonomous): Submits automatically to pre-authorized API endpoints in your allowlist.
• Mode B (Approval Required): Stages documents in your dashboard queue for 1-click review.
• Mode C (Assisted): Pre-fills answers and generates direct portal links for manual submission.

5️⃣ Strict Submission Proof:
Applications are only marked confirmed when an authoritative API receipt or confirmation ID is returned. A browser click alone is never accepted as evidence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 INTERACTIVE COMMAND SHORTCUTS:

• /jobs — View top high-match vacancies live in your pipeline.
• /queue — Inspect applications waiting for your approval.
• /status — System health, active crawling metrics & pipeline counts.
• /profile — View your active candidate credentials & skills.
• /help — Full command and documentation guide.

🖥️ Web Command Center: http://localhost:3000
Status: Background Scheduler Active • Operating in Asia/Kolkata timezone`;

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

  const handleSendTest = async (customText?: string) => {
    setSending(true);
    setSendResult(null);
    try {
      const payload = customText || testMsg;
      const res = await sendTelegramTest(payload);
      setSendResult(res);
    } catch (e) {
      setSendResult({ success: false, error: String(e) });
    } finally {
      setSending(false);
    }
  };

  const handleCopyStart = () => {
    navigator.clipboard.writeText(startMessagePreview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Telegram Bot & Notifications</h2>
        <p className="text-xs text-gray-400">
          High-tier Telegram Bot API integration with automated `/start` command handler, status queries, and high-match alerts.
        </p>
      </div>

      {/* Telegram Status & Quick Test Card */}
      <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surfaceBorder pb-5">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#229ED9]/10 border border-[#229ED9]/30 flex items-center justify-center text-[#229ED9] shadow-lg shadow-[#229ED9]/10">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-white">Telegram Career Agent</h3>
              <p className="text-xs text-gray-400 font-mono">
                {status?.is_configured ? `Active • Chat ID: ${status.chat_id}` : "Ready for Bot Token Configuration"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium border ${
                status?.is_configured
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/20"
              }`}
            >
              {status?.is_configured ? "Live & Polling" : "Simulation Mode (Local)"}
            </span>
          </div>
        </div>

        {/* Dispatch Elite /start Message Button */}
        <div className="p-4 rounded-xl bg-background/60 border border-surfaceBorder flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand" />
              <h4 className="text-xs font-semibold text-white">Test Elite /start Welcome Message</h4>
            </div>
            <p className="text-[11px] text-gray-400">
              Dispatches the full in-depth enterprise architecture message directly to your Telegram chat.
            </p>
          </div>

          <button
            onClick={() => handleSendTest(startMessagePreview)}
            disabled={sending}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-brand to-accent text-slate-950 flex items-center gap-2 shrink-0 transition-all shadow-md shadow-brand/20 hover:opacity-90"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>Send /start to Telegram</span>
          </button>
        </div>

        {/* Custom Test Dispatcher */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-gray-300">Custom Alert Dispatcher</label>
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={testMsg}
              onChange={(e) => setTestMsg(e.target.value)}
              className="flex-1 px-3.5 py-2 rounded-xl bg-background border border-surfaceBorder text-xs text-white focus:outline-none focus:border-brand"
            />
            <button
              onClick={() => handleSendTest()}
              disabled={sending}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-surface border border-surfaceBorder hover:border-gray-500 text-white flex items-center gap-2 shrink-0 transition-all"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>Send Alert</span>
            </button>
          </div>
        </div>

        {/* Send Result Output */}
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
                  <span className="text-red-400 font-medium">Notification feedback logged:</span>
                </>
              )}
            </div>
            <pre className="text-[11px] text-gray-400 font-mono overflow-x-auto bg-surface p-3 rounded-lg border border-surfaceBorder">
              {JSON.stringify(sendResult, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* In-Depth /start Message Preview Pane */}
      <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-brand" />
            <h3 className="font-semibold text-xs text-white uppercase tracking-wider">
              Telegram /start Deep Detail Message Preview
            </h3>
          </div>
          <button
            onClick={handleCopyStart}
            className="text-xs text-gray-400 hover:text-white flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-surfaceBorder bg-background"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>

        <div className="p-4 rounded-xl bg-background/80 border border-surfaceBorder font-mono text-[11px] text-gray-300 leading-relaxed max-h-96 overflow-y-auto whitespace-pre-wrap select-all">
          {startMessagePreview}
        </div>
      </div>

      {/* Interactive Telegram Commands Directory */}
      <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
        <h3 className="font-semibold text-xs text-white uppercase tracking-wider">
          Interactive Bot Commands (Supported via Telegram Chat)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
            <div className="font-mono text-brand font-bold">/start</div>
            <p className="text-[11px] text-gray-300">
              Sends the full high-end enterprise welcome message detailing the 6-pillar matching heuristic, 3 application modes, and value proposition.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
            <div className="font-mono text-emerald-400 font-bold">/jobs</div>
            <p className="text-[11px] text-gray-300">
              Queries your live database and returns the top 5 highest-matching global vacancies with compensation and portal links.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
            <div className="font-mono text-amber-400 font-bold">/queue</div>
            <p className="text-[11px] text-gray-300">
              Displays applications waiting for your approval before submission with application IDs.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
            <div className="font-mono text-accent font-bold">/status</div>
            <p className="text-[11px] text-gray-300">
              Reports live crawling metrics, confirmed submissions, active scheduler state, and pipeline health.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
            <div className="font-mono text-blue-400 font-bold">/profile</div>
            <p className="text-[11px] text-gray-300">
              Prints your active candidate profile, academic credentials (UPES MBA CGPA 8.90, Jamia B.Tech 83.3%), and verifiable skills.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
            <div className="font-mono text-gray-400 font-bold">/help</div>
            <p className="text-[11px] text-gray-300">
              Quick reference guide for all supported bot commands and web dashboard links.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
