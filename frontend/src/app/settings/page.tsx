"use client";
import React, { useEffect, useState } from "react";
import { 
  Sliders, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Save, 
  Loader2, 
  Key, 
  Send, 
  Sparkles, 
  Folder, 
  Clock, 
  Eye, 
  EyeOff 
} from "lucide-react";
import { fetchSettings, updateSettings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>({
    telegram_bot_token: "",
    telegram_chat_id: "",
    gemini_api_key: "",
    resume_folder: "/home/nx-pro",
    timezone: "Asia/Kolkata",
    job_search_interval_hours: 6,
    auto_apply_enabled: false,
    approval_required: true,
    min_match_score: 80,
    max_daily_applications: 10,
    allowed_sources: ["mock_ats", "greenhouse_sandbox"],
    cooling_off_days: 30
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [showTelegramToken, setShowTelegramToken] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchSettings();
        setSettings(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSettings(settings);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-gray-400 text-xs">
        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
        Loading settings & environment variables...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">System Settings & Environment Configuration</h2>
        <p className="text-xs text-gray-400">
          Set environment variables (.env), API credentials, automation policies, and rate limits directly from this panel.
        </p>
      </div>

      <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-8">
        
        {/* SECTION 1: ENVIRONMENT VARIABLES & CREDENTIALS */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 border-b border-surfaceBorder pb-3">
            <Key className="w-4 h-4 text-brand" />
            <h3 className="font-semibold text-sm text-white">Environment Variables & API Keys (.env)</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Telegram Bot Token */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300 flex items-center justify-between">
                <span>TELEGRAM_BOT_TOKEN</span>
                <button
                  type="button"
                  onClick={() => setShowTelegramToken(!showTelegramToken)}
                  className="text-[11px] text-gray-400 hover:text-white flex items-center gap-1"
                >
                  {showTelegramToken ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  <span>{showTelegramToken ? "Hide" : "Show"}</span>
                </button>
              </label>
              <div className="relative">
                <input
                  type={showTelegramToken ? "text" : "password"}
                  placeholder="e.g. 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                  value={settings.telegram_bot_token || ""}
                  onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
                  className="w-full px-3.5 py-2 bg-background/80 border border-surfaceBorder rounded-xl text-xs text-white font-mono placeholder-gray-600 focus:outline-none focus:border-brand"
                />
              </div>
              <p className="text-[10px] text-gray-500">From @BotFather on Telegram for real-time application alerts.</p>
            </div>

            {/* Telegram Chat ID */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300">
                TELEGRAM_CHAT_ID
              </label>
              <input
                type="text"
                placeholder="e.g. 987654321"
                value={settings.telegram_chat_id || ""}
                onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
                className="w-full px-3.5 py-2 bg-background/80 border border-surfaceBorder rounded-xl text-xs text-white font-mono placeholder-gray-600 focus:outline-none focus:border-brand"
              />
              <p className="text-[10px] text-gray-500">Your personal or channel chat ID (from @userinfobot).</p>
            </div>

            {/* Gemini API Key */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300 flex items-center justify-between">
                <span>GEMINI_API_KEY</span>
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="text-[11px] text-gray-400 hover:text-white flex items-center gap-1"
                >
                  {showGeminiKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  <span>{showGeminiKey ? "Hide" : "Show"}</span>
                </button>
              </label>
              <input
                type={showGeminiKey ? "text" : "password"}
                placeholder="AIzaSy..."
                value={settings.gemini_api_key || ""}
                onChange={(e) => setSettings({ ...settings, gemini_api_key: e.target.value })}
                className="w-full px-3.5 py-2 bg-background/80 border border-surfaceBorder rounded-xl text-xs text-white font-mono placeholder-gray-600 focus:outline-none focus:border-brand"
              />
              <p className="text-[10px] text-gray-500">Used for deep semantic matching and document personalization.</p>
            </div>

            {/* Resume Workspace Folder */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300">
                RESUME_FOLDER
              </label>
              <input
                type="text"
                placeholder="/home/nx-pro"
                value={settings.resume_folder || ""}
                onChange={(e) => setSettings({ ...settings, resume_folder: e.target.value })}
                className="w-full px-3.5 py-2 bg-background/80 border border-surfaceBorder rounded-xl text-xs text-white font-mono placeholder-gray-600 focus:outline-none focus:border-brand"
              />
              <p className="text-[10px] text-gray-500">Local directory scanned for candidate resumes (.pdf, .docx, .md).</p>
            </div>

            {/* Timezone */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300">
                TIMEZONE
              </label>
              <input
                type="text"
                placeholder="Asia/Kolkata"
                value={settings.timezone || "Asia/Kolkata"}
                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                className="w-full px-3.5 py-2 bg-background/80 border border-surfaceBorder rounded-xl text-xs text-white font-mono placeholder-gray-600 focus:outline-none focus:border-brand"
              />
              <p className="text-[10px] text-gray-500">Default schedule and timestamp display timezone.</p>
            </div>

            {/* Job Search Interval */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300">
                JOB_SEARCH_INTERVAL_HOURS
              </label>
              <input
                type="number"
                min="1"
                max="24"
                value={settings.job_search_interval_hours || 6}
                onChange={(e) => setSettings({ ...settings, job_search_interval_hours: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-background/80 border border-surfaceBorder rounded-xl text-xs text-white font-mono focus:outline-none focus:border-brand"
              />
              <p className="text-[10px] text-gray-500">Interval for automated background crawling and verification.</p>
            </div>
          </div>
        </div>

        {/* SECTION 2: APPLICATION MODES & AUTOMATION CONTROLS */}
        <div className="space-y-4 pt-4 border-t border-surfaceBorder">
          <div className="flex items-center gap-2 border-b border-surfaceBorder pb-3">
            <Sliders className="w-4 h-4 text-accent" />
            <h3 className="font-semibold text-sm text-white">Application Modes & Safety Policies</h3>
          </div>

          {/* Mode A Policy Control */}
          <div className="p-5 rounded-xl bg-background/50 border border-surfaceBorder space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <h4 className="font-semibold text-xs text-white">Mode A: Fully Autonomous Submission (AUTO_APPLY_ENABLED)</h4>
                </div>
                <p className="text-xs text-gray-400 max-w-xl">
                  When enabled, the system autonomously submits applications without manual intervention for verified sources in your allowlist.
                </p>
              </div>

              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={settings.auto_apply_enabled}
                  onChange={(e) => setSettings({ ...settings, auto_apply_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
              </label>
            </div>

            {settings.auto_apply_enabled && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>
                  Autonomous submissions are strictly constrained to sources in your Authorized Sources Allowlist.
                </span>
              </div>
            )}
          </div>

          {/* Mode B: Approval Required */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-background/50 border border-surfaceBorder">
            <div className="space-y-0.5">
              <h4 className="text-xs font-semibold text-white">Mode B: Require Manual Approval (APPLICATION_APPROVAL_REQUIRED)</h4>
              <p className="text-[11px] text-gray-400">
                Stages generated application documents in your Approval Queue for inspection before sending.
              </p>
            </div>
            <input
              type="checkbox"
              checked={settings.approval_required}
              onChange={(e) => setSettings({ ...settings, approval_required: e.target.checked })}
              className="rounded border-gray-700 text-brand focus:ring-brand w-4 h-4 cursor-pointer"
            />
          </div>

          {/* Thresholds & Daily Limits */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-background/50 border border-surfaceBorder space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300 font-medium">MIN_MATCH_SCORE</span>
                <strong className="text-brand font-mono">{settings.min_match_score}/100</strong>
              </div>
              <input
                type="range"
                min="60"
                max="95"
                step="5"
                value={settings.min_match_score}
                onChange={(e) => setSettings({ ...settings, min_match_score: Number(e.target.value) })}
                className="w-full accent-brand cursor-pointer"
              />
              <p className="text-[10px] text-gray-500">Jobs scoring below this threshold are marked review-required or skipped.</p>
            </div>

            <div className="p-4 rounded-xl bg-background/50 border border-surfaceBorder space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300 font-medium">MAX_DAILY_APPLICATIONS</span>
                <strong className="text-brand font-mono">{settings.max_daily_applications} / day</strong>
              </div>
              <input
                type="number"
                min="1"
                max="50"
                value={settings.max_daily_applications}
                onChange={(e) => setSettings({ ...settings, max_daily_applications: Number(e.target.value) })}
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-surfaceBorder text-xs text-white font-mono focus:outline-none focus:border-brand"
              />
              <p className="text-[10px] text-gray-500">Anti-spam velocity governor to maintain submission quality.</p>
            </div>
          </div>
        </div>

        {/* Save Bar */}
        <div className="pt-4 border-t border-surfaceBorder flex items-center justify-between">
          <div>
            {savedSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium animate-pulse">
                <CheckCircle2 className="w-4 h-4" />
                Environment variables (.env) & settings saved successfully!
              </span>
            )}
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-brand hover:bg-brandDark text-slate-950 flex items-center gap-2 transition-all shadow-lg shadow-brand/20"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            <span>Save Settings & .env</span>
          </button>
        </div>

      </div>
    </div>
  );
}
