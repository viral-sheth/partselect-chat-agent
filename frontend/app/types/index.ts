// Matches backend schemas exactly

export interface Product {
  part_number: string;
  name: string;
  price: number | null;
  image_url: string | null;
  product_url: string | null;
  in_stock: boolean;
  brand: string | null;
  category: string;
  description: string | null;
}

export interface CompatibilityResult {
  part_number: string;
  model_number: string;
  is_compatible: boolean;
  notes: string;
  alternative_parts: string[];
}

export interface TroubleshootingResult {
  symptom: string;
  appliance_type: string;
  likely_causes: string[];
  recommended_parts: Product[];
  repair_tips: string[];
}

export interface InstallationGuide {
  part_number: string;
  found: boolean;
  guide_text: string;
  source_url: string | null;
  difficulty: string;
}

export interface CartItem {
  part_number: string;
  name: string;
  price: number | null;
  quantity: number;
  image_url: string | null;
}

export interface CartResult {
  success: boolean;
  message: string;
  items: CartItem[];
  subtotal: number;
  item_count: number;
}

// SSE event types streamed from the backend
export type SSEEvent =
  | { type: "text"; content: string }
  | { type: "tool_start"; tool: string }
  | { type: "tool_result"; tool: string; result: Record<string, unknown> }
  | { type: "done"; final_messages: unknown[] }
  | { type: "error"; content: string };

// Chat message for the UI
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolResults?: ToolResult[];
  isStreaming?: boolean;
}

export interface ToolResult {
  tool: string;
  result: Record<string, unknown>;
}
