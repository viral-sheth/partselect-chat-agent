"use client";

import { InstallationGuide } from "@/app/types";
import { Wrench, ExternalLink } from "lucide-react";

const DIFFICULTY_STYLES: Record<string, string> = {
  easy: "bg-green-100 text-green-700",
  moderate: "bg-[#FFB800]/20 text-yellow-800",
  hard: "bg-red-100 text-red-700",
  unknown: "bg-gray-100 text-gray-600",
};

export function InstallationGuideCard({ guide }: { guide: InstallationGuide }) {
  const difficulty = (guide.difficulty || "unknown").toLowerCase();
  const badgeStyle = DIFFICULTY_STYLES[difficulty] || DIFFICULTY_STYLES.unknown;

  // Support both steps[] array (new) and guide_text string (legacy)
  const steps: string[] = (guide as any).steps
    ? (guide as any).steps
    : (guide.guide_text || "")
        .split(/\n+/)
        .map((l: string) => l.trim())
        .filter(Boolean);

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Wrench size={15} className="text-[#2E7D32]" />
          <span className="text-sm font-semibold text-gray-900">
            Installation Guide
          </span>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeStyle}`}>
          {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
        </span>
      </div>

      <p className="text-xs text-gray-500 mb-3">
        Part # {guide.part_number}
        {(guide as any).part_name && ` — ${(guide as any).part_name}`}
      </p>

      {/* Numbered steps */}
      <ol className="space-y-2">
        {steps.map((step, i) => (
          <li key={i} className="flex gap-2 text-sm text-gray-700 leading-relaxed">
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#2E7D32] text-white text-xs flex items-center justify-center font-bold mt-0.5">
              {i + 1}
            </span>
            <span>{step.replace(/^\d+\.\s*/, "")}</span>
          </li>
        ))}
      </ol>

      {(guide as any).notes && (
        <p className="text-xs text-gray-400 mt-3 italic">{(guide as any).notes}</p>
      )}

      {guide.source_url && (
        <a
          href={guide.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1 text-xs text-[#2E7D32] hover:underline"
        >
          <ExternalLink size={12} />
          View on PartSelect
        </a>
      )}
    </div>
  );
}
