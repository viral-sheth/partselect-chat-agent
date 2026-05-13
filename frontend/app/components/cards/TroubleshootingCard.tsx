"use client";

import { AlertTriangle, Wrench } from "lucide-react";

interface TroubleshootingCardProps {
  result: {
    symptom: string;
    likely_causes: string[];
    repair_tips: string[];
  };
}

export function TroubleshootingCard({ result }: TroubleshootingCardProps) {
  return (
    <div className="border border-amber-200 bg-amber-50 rounded-lg p-4 w-full">
      <div className="flex items-center gap-2 mb-2">
        <Wrench className="text-amber-600" size={20} />
        <span className="font-semibold text-sm text-amber-800">
          Troubleshooting: {result.symptom}
        </span>
      </div>

      {result.likely_causes.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-medium text-gray-700 mb-1">
            Likely Causes:
          </p>
          <ul className="space-y-1">
            {result.likely_causes.map((cause, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-gray-600">
                <AlertTriangle size={12} className="text-amber-500 mt-0.5 flex-shrink-0" />
                {cause}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.repair_tips.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-700 mb-1">
            Repair Tips:
          </p>
          <ol className="space-y-1 list-decimal list-inside">
            {result.repair_tips.map((tip, i) => (
              <li key={i} className="text-xs text-gray-600">
                {tip}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
