"use client";

import { useState } from "react";
import { Product } from "@/app/types";
import { ShoppingCart, ExternalLink, CheckCircle, XCircle, Package } from "lucide-react";

interface ProductCardProps {
  product: Product;
  onAddToCart?: (partNumber: string) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const [imgFailed, setImgFailed] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg p-3 bg-white shadow-sm hover:shadow-md transition-shadow w-full">
      <div className="flex gap-3">
        {/* Product Image */}
        <div className="flex-shrink-0 w-20 h-20 bg-gray-50 rounded overflow-hidden flex items-center justify-center">
          {product.image_url && !imgFailed ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-contain"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <Package size={28} className="text-gray-300" />
          )}
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-sm text-gray-900 line-clamp-2">
            {product.name}
          </h4>
          <p className="text-xs text-gray-500 mt-0.5">
            Part # {product.part_number}
          </p>

          {/* Price + Stock */}
          <div className="flex items-center gap-2 mt-1">
            {product.price !== null && (
              <span className="text-lg font-bold text-gray-900">
                ${product.price.toFixed(2)}
              </span>
            )}
            <span
              className={`flex items-center gap-0.5 text-xs ${
                product.in_stock ? "text-green-600" : "text-red-500"
              }`}
            >
              {product.in_stock ? (
                <>
                  <CheckCircle size={12} /> In Stock
                </>
              ) : (
                <>
                  <XCircle size={12} /> Out of Stock
                </>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      {product.description && (
        <p className="text-xs text-gray-600 mt-2 line-clamp-2">
          {product.description}
        </p>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => onAddToCart?.(product.part_number)}
          disabled={!product.in_stock}
          className="flex-1 flex items-center justify-center gap-1.5 bg-[#2E7D32] text-white text-xs font-medium py-2 px-3 rounded hover:bg-[#1b5e20] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <ShoppingCart size={14} />
          Add to Cart
        </button>
        {product.product_url && (
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1 border border-gray-300 text-gray-600 text-xs py-2 px-3 rounded hover:bg-gray-50 transition-colors"
          >
            <ExternalLink size={14} />
            View
          </a>
        )}
      </div>
    </div>
  );
}
