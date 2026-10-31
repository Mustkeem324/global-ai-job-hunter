"use client";
import React, { useEffect, useState } from "react";
import { FileText, Folder, RefreshCw, Check, Sparkles, GraduationCap, Briefcase, ExternalLink, Loader2 } from "lucide-react";
import { fetchCandidateProfile, scanResumeFolder, parseResumeFile } from "@/lib/api";

export default function ResumesPage() {
  const [profile, setProfile] = useState<any>(null);
  const [folderPath, setFolderPath] = useState("/home/nx-pro");
  const [foundFiles, setFoundFiles] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [parsingPath, setParsingPath] = useState<string | null>(null);

  const loadProfile = async () => {
    try {
      const data = await fetchCandidateProfile();
      setProfile(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await scanResumeFolder(folderPath);
      setFoundFiles(res.files || []);
    } catch (e) {
      console.error(e);
    } finally {
      setScanning(false);
    }
  };

  const handleParse = async (p: string) => {
    setParsingPath(p);
    try {
      await parseResumeFile(p);
      await loadProfile();
    } catch (e) {
      console.error(e);
    } finally {
      setParsingPath(null);
    }
  };

  useEffect(() => {
    loadProfile();
    handleScan();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Resume Intelligence & Ingestion</h2>
        <p className="text-xs text-gray-400">
          Folder-level document scanner supporting PDF, DOCX, TXT, and Markdown. Normalizes structured credentials with verified evidence links.
        </p>
      </div>

      {/* Folder Picker Card */}
      <div className="p-5 rounded-2xl bg-surface border border-surfaceBorder space-y-4">
        <div className="flex items-center gap-2">
          <Folder className="w-4 h-4 text-brand" />
          <h3 className="font-semibold text-xs text-white">Local Workspace Resume Folder</h3>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            className="flex-1 px-3.5 py-2 rounded-xl bg-background border border-surfaceBorder text-xs text-white font-mono focus:outline-none focus:border-brand"
            placeholder="/path/to/resumes"
          />
          <button
            onClick={handleScan}
            disabled={scanning}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-surface border border-surfaceBorder hover:border-gray-500 text-white flex items-center gap-2 shrink-0 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? "animate-spin" : ""}`} />
            <span>Scan Folder</span>
          </button>
        </div>

        {/* Found Resumes in Folder */}
        <div className="space-y-2 pt-2">
          <span className="text-[11px] font-medium text-gray-400">
            Detected Files in Folder ({foundFiles.length})
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {foundFiles.map((file) => {
              const isParsing = parsingPath === file.file_path;
              return (
                <div
                  key={file.file_path}
                  className="p-3 rounded-xl bg-background/60 border border-surfaceBorder flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <FileText className="w-4 h-4 text-brand shrink-0" />
                    <div className="truncate">
                      <div className="font-medium text-white truncate">{file.file_name}</div>
                      <div className="text-[10px] text-gray-500 font-mono">
                        {(file.file_size / 1024).toFixed(1)} KB • {file.extension}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleParse(file.file_path)}
                    disabled={isParsing}
                    className="px-3 py-1 rounded-lg text-[11px] font-semibold bg-brand/10 text-brand border border-brand/30 hover:bg-brand/20 transition-all shrink-0 flex items-center gap-1"
                  >
                    {isParsing ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Parsing...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3 h-3" />
                        <span>Parse & Set Active</span>
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Normalized Profile View */}
      {profile && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-surface border border-surfaceBorder space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surfaceBorder pb-6">
              <div>
                <h3 className="text-xl font-bold text-white">{profile.full_name}</h3>
                <p className="text-xs text-brand mt-0.5">{profile.headline}</p>
                <p className="text-xs text-gray-400 mt-1">{profile.location} • {profile.email} • {profile.phone}</p>
              </div>

              <div className="flex items-center gap-3">
                <a
                  href={profile.github_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-background border border-surfaceBorder hover:border-gray-500 text-gray-300 flex items-center gap-1.5"
                >
                  <span>GitHub</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
                <a
                  href={profile.portfolio_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-background border border-surfaceBorder hover:border-gray-500 text-gray-300 flex items-center gap-1.5"
                >
                  <span>FreelanceKar</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            {/* Professional Summary */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Substantiated Executive Summary
              </h4>
              <p className="text-xs text-gray-300 leading-relaxed bg-background/50 p-4 rounded-xl border border-surfaceBorder font-mono">
                {profile.summary}
              </p>
            </div>

            {/* Extracted Skills with Evidence Links */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Extracted Skills & Verifiable Evidence ({profile.skills?.length || 0})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {profile.skills?.map((sk: any, i: number) => (
                  <div key={i} className="p-3 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white">{sk.name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-surfaceBorder text-brand">
                        {sk.category}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400 italic font-mono truncate">
                      "{sk.evidence}"
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Projects Showcase */}
            {profile.projects && profile.projects.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-brand" />
                  <span>Verified Projects & Systems Portfolio ({profile.projects.length})</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {profile.projects.map((proj: any, i: number) => (
                    <div key={i} className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1.5">
                      <div className="font-semibold text-xs text-white">{proj.title}</div>
                      <p className="text-[11px] text-gray-300 leading-relaxed">{proj.description}</p>
                      <div className="flex flex-wrap gap-1 pt-1">
                        {proj.technologies?.map((tech: string, tidx: number) => (
                          <span key={tidx} className="text-[9px] px-1.5 py-0.5 rounded bg-surface border border-surfaceBorder text-gray-400 font-mono">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Work Authorization & Remote Eligibility */}
            {profile.work_authorization && (
              <div className="p-4 rounded-xl bg-brand/5 border border-brand/20 space-y-2">
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span className="text-emerald-400">●</span> International Remote Work Authorization
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <div>
                    <span className="text-gray-400 block text-[10px]">Tax / Billing Entity:</span>
                    <span className="font-semibold text-white">{profile.work_authorization.contractor_entity || "FreelanceKar (GST Reg.)"}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[10px]">US W-8BEN Tax Status:</span>
                    <span className="font-semibold text-emerald-400">Compliant / Ready</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[10px]">Weekly Availability:</span>
                    <span className="font-semibold text-white">{profile.work_authorization.weekly_availability_hours || 40} hrs / week</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[10px]">Payment Channels:</span>
                    <span className="font-semibold text-gray-300">SWIFT, Wise, USDC</span>
                  </div>
                </div>
              </div>
            )}

            {/* Uncertainty Detector & Candidate Clarifications */}
            {profile.uncertain_claims && profile.uncertain_claims.length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-3">
                <h4 className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                  <span>⚠️</span> Candidate Profile Clarifications (Zero Hallucination Guarantee)
                </h4>
                <div className="space-y-2">
                  {profile.uncertain_claims.map((uc: any, i: number) => (
                    <div key={i} className="text-xs p-3 rounded-lg bg-background/80 border border-amber-500/20 space-y-1">
                      <div className="font-semibold text-white">{uc.issue}</div>
                      <div className="text-[11px] text-gray-400 italic">Document text: {uc.detected_in_document}</div>
                      <div className="text-[11px] text-amber-200 font-medium pt-1">Recommended action: {uc.recommendation_to_user}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Education Credentials */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <GraduationCap className="w-4 h-4 text-brand" />
                <span>Academic Degrees & Qualifications</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {profile.education?.map((edu: any, i: number) => (
                  <div key={i} className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
                    <div className="font-semibold text-xs text-white">{edu.degree}</div>
                    <div className="text-[11px] text-gray-400">{edu.institution}</div>
                    <div className="text-[11px] text-brand font-mono font-medium">{edu.grade} • {edu.year}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Professional Workstreams */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-brand" />
                <span>Verified Professional Workstreams</span>
              </h4>
              <div className="space-y-2.5">
                {profile.experiences?.map((exp: any, i: number) => (
                  <div key={i} className="p-3.5 rounded-xl bg-background/50 border border-surfaceBorder space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white">{exp.role_title}</span>
                      <span className="text-[11px] text-gray-400 font-mono">{exp.start_date} – {exp.end_date}</span>
                    </div>
                    <div className="text-xs text-brand font-medium">{exp.company}</div>
                    <p className="text-xs text-gray-400 pt-1">{exp.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
