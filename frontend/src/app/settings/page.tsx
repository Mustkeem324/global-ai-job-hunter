"use client";
import React, { useEffect, useState } from "react";
import { Sliders, ShieldAlert, CheckCircle2, AlertTriangle, Save, Loader2 } from "lucide-react";
import { fetchSettings, updateSettings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>({
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
      setTimeout(() => setSavedSuccess(false), 3000);
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
        Loading settings...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Automation & Compliance Policies</h2>
        <p className="text-xs text-gray-400">
          Configure matching thresholds, daily submission limits, and application authorization controls.
        </p>
      </div>

      <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-6">
        {/* Mode A Policy Control */}
        <div className="p-5 rounded-xl bg-background/50 border border-surfaceBorder space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="font-semibold text-sm text-white">Mode A: Fully Autonomous Submission</h3>
              </div>
              <p className="text-xs text-gray-400 max-w-xl">
                When enabled, the system autonomously submits applications only to sources explicitly allowed in your allowlist without manual intervention.
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
            <h4 className="text-xs font-semibold text-white">Mode B: Require Manual Approval Before Submission</h4>
            <p className="text-[11px] text-gray-400">
              Stages generated application documents in your Approval Queue for inspection before sending.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.approval_required}
            onChange={(e) => setSettings({ ...settings, approval_required: e.target.checked })}
            className="rounded border-gray-700 text-brand focus:ring-brand"
          />
        </div>

        {/* Sliders & Caps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-background/50 border border-surfaceBorder space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-300 font-medium">Minimum Match Threshold</span>
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
              <span className="text-gray-300 font-medium">Max Daily Applications</span>
              <strong className="text-brand font-mono">{settings.max_daily_applications} / day</strong>
            </div>
            <input
              type="number"
              min="1"
              max="50"
              value={settings.max_daily_applications}
              onChange={(e) => setSettings({ ...settings, max_daily_applications: Number(e.target.value) })}
              className="w-full px-3 py-1.5 rounded-lg bg-background border border-surfaceBorder text-xs text-white"
            />
            <p className="text-[10px] text-gray-500">Anti-spam velocity governor to maintain submission quality.</p>
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-4 border-t border-surfaceBorder flex items-center justify-between">
          <div>
            {savedSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                Settings saved successfully!
              </span>
            )}
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-brand hover:bg-brandDark text-slate-950 flex items-center gap-2 transition-all shadow-md"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            <span>Save Configuration</span>
          </button>
        </div>
      </div>
    </div>
  );
}
