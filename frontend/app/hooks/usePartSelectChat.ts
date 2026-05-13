"use client";

import { useState, useCallback, useRef } from "react";
import { ChatMessage, ToolResult, SSEEvent, CartItem } from "@/app/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

export function usePartSelectChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartSubtotal, setCartSubtotal] = useState(0);
  const sessionIdRef = useRef<string>(generateId());

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message
    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content: content.trim(),
    };

    // Add placeholder assistant message for streaming
    const assistantMsg: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      toolResults: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    setActiveTools([]);

    try {
      const response = await fetch(`${API_URL}/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content.trim(),
          session_id: sessionIdRef.current,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Keep incomplete chunk

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;

          try {
            const event: SSEEvent = JSON.parse(trimmed.slice(6));

            switch (event.type) {
              case "text":
                setMessages((prev) => {
                  const lastIdx = prev.length - 1;
                  const last = prev[lastIdx];
                  if (last?.role !== "assistant") return prev;
                  return [
                    ...prev.slice(0, lastIdx),
                    { ...last, content: last.content + event.content },
                  ];
                });
                break;

              case "tool_start":
                setActiveTools((prev) => [...prev, event.tool]);
                break;

              case "tool_result":
                setActiveTools((prev) =>
                  prev.filter((t) => t !== event.tool)
                );
                // Update cart state when cart tools respond
                if (
                  event.tool === "add_to_cart" ||
                  event.tool === "get_cart"
                ) {
                  const r = event.result as {
                    items?: CartItem[];
                    subtotal?: number;
                  };
                  if (r.items) setCartItems(r.items);
                  if (r.subtotal != null) setCartSubtotal(r.subtotal);
                }
                setMessages((prev) => {
                  const lastIdx = prev.length - 1;
                  const last = prev[lastIdx];
                  if (last?.role !== "assistant") return prev;
                  const newResult: ToolResult = {
                    tool: event.tool,
                    result: event.result,
                  };
                  return [
                    ...prev.slice(0, lastIdx),
                    {
                      ...last,
                      toolResults: [...(last.toolResults || []), newResult],
                    },
                  ];
                });
                break;

              case "done":
                setMessages((prev) => {
                  const lastIdx = prev.length - 1;
                  const last = prev[lastIdx];
                  if (last?.role !== "assistant") return prev;
                  return [
                    ...prev.slice(0, lastIdx),
                    { ...last, isStreaming: false },
                  ];
                });
                break;

              case "error":
                setMessages((prev) => {
                  const lastIdx = prev.length - 1;
                  const last = prev[lastIdx];
                  if (last?.role !== "assistant") return prev;
                  return [
                    ...prev.slice(0, lastIdx),
                    {
                      ...last,
                      content: `Error: ${event.content}`,
                      isStreaming: false,
                    },
                  ];
                });
                break;
            }
          } catch {
            // Skip malformed events
          }
        }
      }
    } catch (error) {
      setMessages((prev) => {
        const lastIdx = prev.length - 1;
        const last = prev[lastIdx];
        if (last?.role !== "assistant") return prev;
        return [
          ...prev.slice(0, lastIdx),
          {
            ...last,
            content: "Sorry, I'm having trouble connecting. Please try again.",
            isStreaming: false,
          },
        ];
      });
    } finally {
      setIsLoading(false);
      setActiveTools([]);
    }
  }, [isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCartItems([]);
    setCartSubtotal(0);
    sessionIdRef.current = generateId();
  }, []);

  return {
    messages,
    isLoading,
    activeTools,
    cartItems,
    cartSubtotal,
    sendMessage,
    clearMessages,
    sessionId: sessionIdRef.current,
  };
}
