"use client";

import { List, type RowComponentProps } from "react-window";
import { ProductListRow, productListColumnsGrid } from "@/components/ProductListRow";
import type { Product } from "@/lib/types";

export const ITEM_HEIGHT = 57;

interface RowProps {
  products: Product[];
}

function Row({ index, style, products, ariaAttributes }: RowComponentProps<RowProps>) {
  const product = products[index];
  const isLastRow = index === products.length - 1;
  return (
    <div style={style} className="pr-4" {...ariaAttributes}>
      <ProductListRow
        product={product}
        className={isLastRow ? "border-b-0" : undefined}
      />
    </div>
  );
}

interface VirtualizedProductListProps {
  products: Product[];
  height?: number;
  width?: number | string;
}

export function VirtualizedProductList({
  products,
  height = 600,
  width = "100%",
}: VirtualizedProductListProps) {
  if (products.length === 0) return null;

  return (
    <div className="w-full">
      <header
        role="rowgroup"
        className="sticky top-0 z-10 bg-background pr-4 [&_[role=row]]:border-b"
      >
        <div
          role="row"
          className={`grid border-b transition-colors hover:bg-muted/50 ${productListColumnsGrid}`}
        >
          <div
            role="columnheader"
            className="text-foreground flex h-10 items-center px-2 text-left align-middle font-medium whitespace-nowrap"
          >
            <div className="flex items-center gap-1">Image</div>
          </div>
          <div
            role="columnheader"
            className="text-foreground flex h-10 min-w-0 items-center px-2 text-left align-middle font-medium whitespace-nowrap"
          >
            <div className="flex items-center gap-1">Title</div>
          </div>
          <div
            role="columnheader"
            className="text-foreground flex h-10 min-w-0 items-center px-2 text-left align-middle font-medium whitespace-nowrap"
          >
            <div className="flex items-center gap-1">Brand</div>
          </div>
        </div>
      </header>
      <List<RowProps>
        rowCount={products.length}
        rowHeight={ITEM_HEIGHT}
        rowProps={{ products }}
        rowComponent={Row}
        style={{ height, width: width ?? "100%", overflowX: "hidden" }}
      />
    </div>
  );
}
