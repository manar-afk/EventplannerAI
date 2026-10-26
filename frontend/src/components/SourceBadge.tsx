import React from "react";
import { PlanSource } from "../repository/types";

interface SourceBadgeProps {
  source: PlanSource;
  explanation?: string;
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ source, explanation }) => {
  if (source === "gemini") {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm" title={explanation || "Generated with Google Gemini"}>
        <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
        <span>AI Generated (Gemini)</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300 shadow-sm" title={explanation || "Generated using deterministic Indian event rules"}>
      <span className="w-2 h-2 rounded-full bg-amber-600"></span>
      <span>Rule-Based Plan (Fallback)</span>
    </div>
  );
};
