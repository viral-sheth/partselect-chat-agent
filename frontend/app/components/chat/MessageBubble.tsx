"use client";

import { ChatMessage, Product } from "@/app/types";
import { ProductCard } from "@/app/components/cards/ProductCard";
import { CompatibilityCard } from "@/app/components/cards/CompatibilityCard";
import { TroubleshootingCard } from "@/app/components/cards/TroubleshootingCard";
import { InstallationGuideCard } from "@/app/components/cards/InstallationGuideCard";
import { OrderStatusCard } from "@/app/components/cards/OrderStatusCard";
import { Bot, User } from "lucide-react";

/** Renders inline markdown: **bold**, *italic*, `code` */
function renderInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[2] !== undefined) parts.push(<strong key={m.index}>{m[2]}</strong>);
    else if (m[3] !== undefined) parts.push(<em key={m.index}>{m[3]}</em>);
    else if (m[4] !== undefined)
      parts.push(
        <code key={m.index} className="bg-gray-200 px-1 rounded text-xs font-mono">
          {m[4]}
        </code>
      );
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

/** Converts markdown text to JSX — handles bold, italic, code, bullet lists, numbered lists */
function MarkdownText({ content }: { content: string }) {
  const lines = content.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Blank line → spacing handled by gap
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Headings ## and ###
    if (/^#{1,3}\s/.test(line.trim())) {
      const level = (line.match(/^(#{1,3})\s/) || [])[1]?.length || 2;
      const text = line.trim().replace(/^#{1,3}\s/, "");
      const cls = level === 1
        ? "text-base font-bold text-gray-900 mt-2"
        : level === 2
        ? "text-sm font-bold text-gray-800 mt-2"
        : "text-sm font-semibold text-gray-700 mt-1";
      nodes.push(<p key={i} className={cls}>{renderInline(text)}</p>);
      i++;
      continue;
    }

    // Unordered list block
    if (/^[\*\-]\s/.test(line.trim())) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^[\*\-]\s/.test(lines[i].trim())) {
        const text = lines[i].trim().replace(/^[\*\-]\s/, "");
        items.push(<li key={i}>{renderInline(text)}</li>);
        i++;
      }
      nodes.push(
        <ul key={`ul-${i}`} className="list-disc list-inside space-y-0.5 my-1">
          {items}
        </ul>
      );
      continue;
    }

    // Numbered list block
    if (/^\d+\.\s/.test(line.trim())) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        const text = lines[i].trim().replace(/^\d+\.\s/, "");
        items.push(<li key={i}>{renderInline(text)}</li>);
        i++;
      }
      nodes.push(
        <ol key={`ol-${i}`} className="list-decimal list-inside space-y-0.5 my-1">
          {items}
        </ol>
      );
      continue;
    }

    // Normal paragraph line
    nodes.push(
      <p key={i} className="leading-relaxed">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return <div className="space-y-1 text-sm">{nodes}</div>;
}

interface MessageBubbleProps {
  message: ChatMessage;
  onAddToCart?: (partNumber: string) => void;
}

export function MessageBubble({ message, onAddToCart }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-gray-200" : "bg-[#2E7D32]"
        }`}
      >
        {isUser ? (
          <User size={16} className="text-gray-600" />
        ) : (
          <Bot size={16} className="text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? "text-right" : ""}`}>
        <div
          className={`inline-block rounded-2xl px-4 py-2.5 text-sm ${
            isUser
              ? "bg-[#FFB800] text-gray-900 rounded-tr-sm"
              : "bg-gray-100 text-gray-800 rounded-tl-sm"
          }`}
        >
          {/* Text Content */}
          {message.content && (
            isUser
              ? <div className="whitespace-pre-wrap text-sm">{message.content}</div>
              : <MarkdownText content={message.content} />
          )}

          {/* Streaming cursor */}
          {message.isStreaming && !message.content && (
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
            </div>
          )}
        </div>

        {/* Tool Results — rendered below the text bubble */}
        {message.toolResults && message.toolResults.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.toolResults.map((tr, idx) => (
              <div key={idx}>
                {tr.tool === "search_products" && renderProductResults(tr.result, onAddToCart)}
                {tr.tool === "check_compatibility" && (
                  <CompatibilityCard result={tr.result as any} />
                )}
                {tr.tool === "get_troubleshooting" && (
                  <TroubleshootingCard result={tr.result as any} />
                )}
                {tr.tool === "get_installation_guide" && (
                  <InstallationGuideCard guide={tr.result as any} />
                )}
                {tr.tool === "get_order_status" && (
                  <OrderStatusCard result={tr.result} />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function renderProductResults(
  result: Record<string, unknown>,
  onAddToCart?: (partNumber: string) => void
) {
  const products = (result.products as Product[]) || [];
  if (products.length === 0) return null;

  return (
    <div className="space-y-2">
      {products.map((product) => (
        <ProductCard
          key={product.part_number}
          product={product}
          onAddToCart={onAddToCart}
        />
      ))}
    </div>
  );
}
