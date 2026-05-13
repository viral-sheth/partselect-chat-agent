"use client";

import { X, ShoppingCart, Trash2 } from "lucide-react";
import { CartItem } from "@/app/types";

interface CartPanelProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  subtotal: number;
}

export function CartPanel({ isOpen, onClose, items, subtotal }: CartPanelProps) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#FFB800] border-b border-[#FFB800]">
          <div className="flex items-center gap-2">
            <ShoppingCart size={18} className="text-gray-900" />
            <span className="font-semibold text-gray-900 text-sm">Your Cart</span>
            {items.length > 0 && (
              <span className="bg-[#2E7D32] text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-medium">
                {items.reduce((sum, i) => sum + i.quantity, 0)}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-700 hover:text-gray-900 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 space-y-3">
              <ShoppingCart size={40} className="opacity-30" />
              <p className="text-sm">Your cart is empty.</p>
              <p className="text-xs">
                Ask me to find parts and I&apos;ll add them here.
              </p>
            </div>
          ) : (
            <ul className="space-y-3">
              {items.map((item) => (
                <li
                  key={item.part_number}
                  className="flex gap-3 p-3 border border-gray-100 rounded-lg bg-gray-50"
                >
                  {item.image_url && (
                    <div className="flex-shrink-0 w-14 h-14 bg-white rounded border border-gray-200 overflow-hidden">
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-900 line-clamp-2">
                      {item.name}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      #{item.part_number}
                    </p>
                    <div className="flex items-center justify-between mt-1.5">
                      <span className="text-xs text-gray-600">
                        Qty: {item.quantity}
                      </span>
                      {item.price != null && (
                        <span className="text-sm font-semibold text-gray-900">
                          ${(item.price * item.quantity).toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="border-t border-gray-200 p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Subtotal</span>
              <span className="text-base font-bold text-gray-900">
                ${subtotal.toFixed(2)}
              </span>
            </div>
            <button className="w-full bg-[#2E7D32] text-white text-sm font-medium py-2.5 rounded-lg hover:bg-[#1b5e20] transition-colors">
              Checkout
            </button>
            <p className="text-[10px] text-gray-400 text-center">
              Checkout and shipping handled on partselect.com
            </p>
          </div>
        )}
      </div>
    </>
  );
}
