"use client";

import { Search, GitCompare, BookOpen, Wrench, ShoppingCart, Package } from "lucide-react";

const TOOL_LABELS: Record<string, { label: string; icon: React.ReactNode }> = {
  search_products: {
    label: "Searching for parts...",
    icon: <Search size={14} className="animate-pulse" />,
  },
  check_compatibility: {
    label: "Checking compatibility...",
    icon: <GitCompare size={14} className="animate-pulse" />,
  },
  get_installation_guide: {
    label: "Finding installation guide...",
    icon: <BookOpen size={14} className="animate-pulse" />,
  },
  get_troubleshooting: {
    label: "Diagnosing the issue...",
    icon: <Wrench size={14} className="animate-pulse" />,
  },
  add_to_cart: {
    label: "Adding to cart...",
    icon: <ShoppingCart size={14} className="animate-pulse" />,
  },
  get_cart: {
    label: "Loading cart...",
    icon: <ShoppingCart size={14} className="animate-pulse" />,
  },
  get_order_status: {
    label: "Looking up order...",
    icon: <Package size={14} className="animate-pulse" />,
  },
};

interface ToolStatusProps {
  activeTools: string[];
}

export function ToolStatus({ activeTools }: ToolStatusProps) {
  if (activeTools.length === 0) return null;

  return (
    <div className="flex flex-col gap-1 px-4 py-2">
      {activeTools.map((tool) => {
        const config = TOOL_LABELS[tool] || {
          label: "Processing...",
          icon: <Search size={14} className="animate-pulse" />,
        };
        return (
          <div
            key={tool}
            className="flex items-center gap-2 text-xs text-gray-500"
          >
            {config.icon}
            <span>{config.label}</span>
          </div>
        );
      })}
    </div>
  );
}
