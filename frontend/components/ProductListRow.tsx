"use client";

import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";
import type { Product } from "@/lib/types";

const COLUMNS_GRID = "grid-cols-[80px_1fr_1fr]";

const tableCellClass =
  "p-2 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]";

export function ProductListRow({
  product,
  className,
}: {
  product: Product;
  className?: string;
}) {
  const imageUrls = product.image_urls
    ? product.image_urls.split("|").filter(Boolean)
    : [];
  const firstImage = imageUrls[0];
  const productSlug = encodeURIComponent(product.filename);
  const brandSlug = encodeURIComponent(product.brand);

  return (
    <li
      role="row"
      className={cn(
        "grid h-[57px] items-center border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted",
        COLUMNS_GRID,
        className
      )}
    >
      <div role="cell" className={cn("flex items-center", tableCellClass)}>
        {firstImage ? (
          <Image
            src={firstImage}
            alt={product.name}
            width={40}
            height={40}
            className="h-10 w-10 rounded object-contain"
            loading="lazy"
            unoptimized
          />
        ) : (
          <div className="h-10 w-10 shrink-0 rounded bg-muted" />
        )}
      </div>
      <div role="cell" className={cn("min-w-0 truncate", tableCellClass)}>
        <Link
          href={`/product/${productSlug}`}
          className="cursor-pointer hover:underline"
        >
          {product.name}
        </Link>
      </div>
      <div role="cell" className={cn("min-w-0 truncate", tableCellClass)}>
        <Link
          href={`/brand/${brandSlug}`}
          className="cursor-pointer hover:underline"
        >
          {product.brand}
        </Link>
      </div>
    </li>
  );
}

export const productListColumnsGrid = COLUMNS_GRID;
