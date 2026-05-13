"use client";

import { useRef, useEffect, useState } from "react";
import { usePartSelectChat } from "@/app/hooks/usePartSelectChat";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { SuggestionChips } from "./SuggestionChips";
import { ToolStatus } from "./ToolStatus";
import { CartPanel } from "@/app/components/cart/CartPanel";
import { Wrench, RotateCcw, ShoppingCart } from "lucide-react";

export function ChatWindow() {
  const {
    messages,
    isLoading,
    activeTools,
    cartItems,
    cartSubtotal,
    sendMessage,
    clearMessages,
  } = usePartSelectChat();

  const [isCartOpen, setIsCartOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, activeTools]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-screen w-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#FFB800] bg-[#FFB800]">
        {/* PartSelect Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-[#2E7D32] flex items-center justify-center shadow-sm">
            <Wrench size={20} className="text-white" />
          </div>
          <div className="leading-tight">
            <span className="text-lg font-black tracking-tight text-gray-900">
              Part<span className="text-[#2E7D32]">Select</span>
            </span>
            <p className="text-[11px] text-gray-700 font-medium -mt-0.5">
              AI Parts Assistant
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Cart button */}
          <button
            onClick={() => setIsCartOpen(true)}
            className="relative flex items-center justify-center w-8 h-8 rounded-full bg-white/60 hover:bg-white transition-colors"
          >
            <ShoppingCart size={16} className="text-gray-800" />
            {cartItems.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#2E7D32] text-white text-[10px] rounded-full flex items-center justify-center font-bold">
                {cartItems.reduce((s, i) => s + i.quantity, 0)}
              </span>
            )}
          </button>
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="flex items-center gap-1 text-xs text-gray-700 hover:text-gray-900 transition-colors"
            >
              <RotateCcw size={14} />
              New Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto bg-gray-50"
      >
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {isEmpty ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
              {/* Welcome */}
              <div className="w-16 h-16 rounded-xl bg-[#2E7D32] flex items-center justify-center shadow-md">
                <Wrench size={32} className="text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-800">
                  Welcome to PartSelect
                </h2>
                <p className="text-sm text-gray-500 mt-1 max-w-md">
                  I can help you find the right refrigerator or dishwasher parts,
                  check compatibility, and guide you through installations.
                </p>
              </div>
              <SuggestionChips onSelect={sendMessage} />
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  onAddToCart={(pn) => sendMessage(`Add part ${pn} to my cart`)}
                />
              ))}
              <ToolStatus activeTools={activeTools} />
            </>
          )}
        </div>
      </div>

      {/* Input Bar */}
      <div className="border-t border-gray-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 py-3">
          <InputBar onSend={sendMessage} isLoading={isLoading} />
          <p className="text-[10px] text-gray-400 text-center mt-2">
            PartSelect AI assistant for refrigerator and dishwasher parts only
          </p>
        </div>
      </div>

      {/* Cart Panel */}
      <CartPanel
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        items={cartItems}
        subtotal={cartSubtotal}
      />
    </div>
  );
}
