"use client";
import React, { useState } from "react";
import { Sparkles, RefreshCw, Send } from "lucide-react";
import { triggerJobDiscovery } from "@/lib/api";

export default function Navbar() {
  const [loading, setLoading] = useState(false);

  const handleSyncDiscovery = async () => {
    setLoading(true);
    try {
      await triggerJobDiscovery();
      window.location.reload();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <header className="h-16 border-b border-surfaceBorder bg-surface/70 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Autonomous Engine Active
        </span>
        <span className="text-xs text-gray-400 hidden sm:inline">•</span>
        <span className="text-xs text-gray-400 font-mono hidden sm:inline">Candidate: Mustkeem Ahmad</span>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleSyncDiscovery}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-brand/10 text-brand border border-brand/30 hover:bg-brand/20 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>{loading ? "Discovering..." : "Run Discovery"}</span>
        </button>
      </div>
    </header>
  );
}
