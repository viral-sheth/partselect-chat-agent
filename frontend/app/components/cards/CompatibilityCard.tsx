"use client";

import { CompatibilityResult } from "@/app/types";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";

interface CompatibilityCardProps {
  result: CompatibilityResult;
}

export function CompatibilityCard({ result }: CompatibilityCardProps) {
  const notInCatalog = result.notes?.toLowerCase().includes("not found in our catalog");

  if (notInCatalog) {
    return (
      <div className="border border-amber-200 bg-amber-50 rounded-lg p-4 w-full">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="text-amber-500" size={20} />
          <span className="font-semibold text-sm text-amber-800">Part Not in Catalog</span>
        </div>
        <div className="text-xs text-gray-700 space-y-1">
          <p><span className="font-medium">Part:</span> {result.part_number}</p>
          <p><span className="font-medium">Model:</span> {result.model_number}</p>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          This part number isn't in our current catalog. Try searching by symptom or appliance type to find available parts.
        </p>
      </div>
    );
  }

  return (
    <div
      className={`border rounded-lg p-4 w-full ${
        result.is_compatible
          ? "border-green-200 bg-green-50"
          : "border-red-200 bg-red-50"
      }`}
    >
      {/* Verdict Icon */}
      <div className="flex items-center gap-2 mb-2">
        {result.is_compatible ? (
          <CheckCircle className="text-green-600" size={24} />
        ) : (
          <XCircle className="text-red-500" size={24} />
        )}
        <span
          className={`font-semibold text-sm ${
            result.is_compatible ? "text-green-800" : "text-red-800"
          }`}
        >
          {result.is_compatible ? "Compatible" : "Not Compatible"}
        </span>
      </div>

      {/* Details */}
      <div className="text-xs text-gray-700 space-y-1">
        <p><span className="font-medium">Part:</span> {result.part_number}</p>
        <p><span className="font-medium">Model:</span> {result.model_number}</p>
      </div>

      {/* Notes */}
      <p className="text-xs text-gray-600 mt-2">{result.notes}</p>

      {/* Alternative parts suggestion */}
      {result.alternative_parts.length > 0 && (
        <div className="mt-2 flex items-start gap-1.5">
          <AlertTriangle size={14} className="text-amber-500 mt-0.5" />
          <p className="text-xs text-gray-600">
            Try these alternatives: {result.alternative_parts.join(", ")}
          </p>
        </div>
      )}
    </div>
  );
}
