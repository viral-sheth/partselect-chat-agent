"use client";

interface SuggestionChipsProps {
  onSelect: (suggestion: string) => void;
}

const SUGGESTIONS = [
  "How can I install part number PS11752778?",
  "Is part PS11752778 compatible with model WDT780SAEM1?",
  "The ice maker on my Whirlpool fridge is not working",
  "My dishwasher is not draining properly",
];

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {SUGGESTIONS.map((suggestion) => (
        <button
          key={suggestion}
          onClick={() => onSelect(suggestion)}
          className="text-xs bg-white border border-gray-200 rounded-full px-4 py-2 text-gray-600 hover:bg-[#FFB800]/10 hover:border-[#FFB800] hover:text-[#2E7D32] transition-colors"
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}
