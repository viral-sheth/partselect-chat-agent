"use client";

import { useState, FormEvent, KeyboardEvent } from "react";
import { Send } from "lucide-react";

interface InputBarProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function InputBar({ onSend, isLoading }: InputBarProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-end">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about refrigerator or dishwasher parts..."
        rows={1}
        className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#FFB800] focus:border-transparent placeholder:text-gray-400"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={!input.trim() || isLoading}
        className="flex-shrink-0 w-11 h-11 flex items-center justify-center rounded-xl bg-[#2E7D32] text-white hover:bg-[#1b5e20] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        <Send size={18} />
      </button>
    </form>
  );
}
