"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Search, 
  Layers,
  Clock, 
  CheckCircle2, 
  FileText, 
  Sliders, 
  Bell, 
  BarChart3, 
  ShieldCheck 
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Job Explorer", href: "/jobs", icon: Search },
  { name: "Bulk Applications", href: "/batches", icon: Layers },
  { name: "Application Queue", href: "/queue", icon: Clock },
  { name: "Application History", href: "/history", icon: CheckCircle2 },
  { name: "Resume Intelligence", href: "/resumes", icon: FileText },
  { name: "Automation Settings", href: "/settings", icon: Sliders },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Security & Audit", href: "/security", icon: ShieldCheck }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-surface border-r border-surfaceBorder flex flex-col h-screen sticky top-0 select-none">
      <div className="p-5 border-b border-surfaceBorder flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand to-accent flex items-center justify-center font-bold text-white shadow-lg shadow-brand/20">
          GJ
        </div>
        <div>
          <h1 className="font-semibold text-sm tracking-tight text-white">Global Job Hunter</h1>
          <p className="text-[11px] text-gray-400 font-mono">AUTONOMOUS AI V1.0</p>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-brand/10 text-brand border border-brand/30 shadow-sm"
                  : "text-gray-400 hover:text-white hover:bg-surfaceBorder/40"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-brand" : "text-gray-400"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-surfaceBorder bg-background/50">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-gray-400 font-medium">Scheduler Online (6h cycle)</span>
        </div>
        <p className="text-[10px] text-gray-500 mt-1">Asia/Kolkata timezone active</p>
      </div>
    </aside>
  );
}
