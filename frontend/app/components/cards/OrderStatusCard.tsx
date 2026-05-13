"use client";

import { Package, Truck, CheckCircle, Clock, ExternalLink, XCircle } from "lucide-react";

interface OrderItem {
  name: string;
  quantity: number;
  price: number | null;
}

interface OrderStatusResult {
  found: boolean;
  message?: string;
  order_number?: string;
  status?: string;
  estimated_delivery?: string;
  tracking_url?: string;
  items?: OrderItem[];
  total?: number;
}

const STATUS_CONFIG: Record<
  string,
  { icon: React.ElementType; textColor: string; bgColor: string; label: string }
> = {
  processing: {
    icon: Clock,
    textColor: "text-yellow-700",
    bgColor: "bg-[#FFB800]/15",
    label: "Processing",
  },
  shipped: {
    icon: Truck,
    textColor: "text-blue-700",
    bgColor: "bg-blue-50",
    label: "Shipped",
  },
  delivered: {
    icon: CheckCircle,
    textColor: "text-green-700",
    bgColor: "bg-green-50",
    label: "Delivered",
  },
  cancelled: {
    icon: XCircle,
    textColor: "text-red-700",
    bgColor: "bg-red-50",
    label: "Cancelled",
  },
};

export function OrderStatusCard({
  result,
}: {
  result: Record<string, unknown>;
}) {
  const data = result as unknown as OrderStatusResult;

  if (!data.found) {
    return (
      <div className="border border-red-200 rounded-lg p-4 bg-red-50 w-full">
        <p className="text-sm text-red-700">{data.message}</p>
      </div>
    );
  }

  const statusKey = (data.status || "processing").toLowerCase();
  const config = STATUS_CONFIG[statusKey] || STATUS_CONFIG.processing;
  const StatusIcon = config.icon;
  const items = data.items || [];

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm w-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Package size={15} className="text-[#2E7D32]" />
        <span className="text-sm font-semibold text-gray-900">
          Order #{data.order_number}
        </span>
      </div>

      {/* Status badge */}
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bgColor} mb-3`}
      >
        <StatusIcon size={15} className={config.textColor} />
        <span className={`text-sm font-medium ${config.textColor}`}>
          {config.label}
        </span>
      </div>

      {data.estimated_delivery && (
        <p className="text-xs text-gray-500 mb-3">
          Estimated delivery:{" "}
          <span className="font-medium text-gray-800">
            {data.estimated_delivery}
          </span>
        </p>
      )}

      {/* Items */}
      {items.length > 0 && (
        <div className="border-t border-gray-100 pt-2 space-y-1">
          {items.map((item, i) => (
            <div key={i} className="flex justify-between text-xs text-gray-600">
              <span>
                {item.name} × {item.quantity}
              </span>
              {item.price != null && (
                <span>${(item.price * item.quantity).toFixed(2)}</span>
              )}
            </div>
          ))}
          {data.total != null && (
            <div className="flex justify-between text-sm font-semibold text-gray-900 pt-1.5 border-t border-gray-100 mt-1">
              <span>Total</span>
              <span>${data.total.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {data.tracking_url && (
        <a
          href={data.tracking_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1 text-xs text-[#2E7D32] hover:underline"
        >
          <ExternalLink size={12} />
          Track your package
        </a>
      )}
    </div>
  );
}
