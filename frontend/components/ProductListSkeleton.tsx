"use client";

import { productListColumnsGrid } from "@/components/ProductListRow";
import { Skeleton } from "@/components/ui/skeleton";

const ROW_COUNT = 10;

function TableHeader() {
  return (
    <header
      role="rowgroup"
      className="sticky top-0 z-10 bg-background pr-4 [&_[role=row]]:border-b"
    >
      <div
        role="row"
        className={`grid border-b transition-colors ${productListColumnsGrid}`}
      >
        <div
          role="columnheader"
          className="text-foreground flex h-10 items-center px-2 text-left align-middle font-medium whitespace-nowrap"
        >
          <span>Image</span>
        </div>
        <div
          role="columnheader"
          className="text-foreground flex h-10 min-w-0 items-center px-2 text-left align-middle font-medium whitespace-nowrap"
        >
          <span>Title</span>
        </div>
        <div
          role="columnheader"
          className="text-foreground flex h-10 min-w-0 items-center px-2 text-left align-middle font-medium whitespace-nowrap"
        >
          <span>Brand</span>
        </div>
      </div>
    </header>
  );
}

function SkeletonRow() {
  return (
    <div
      role="row"
      className={`grid h-[57px] items-center border-b border-border ${productListColumnsGrid}`}
    >
      <div className="flex items-center p-2">
        <Skeleton className="h-10 w-10 shrink-0 rounded" />
      </div>
      <div className="flex min-w-0 items-center p-2">
        <Skeleton className="h-4 max-w-[200px] w-3/4" />
      </div>
      <div className="flex min-w-0 items-center p-2">
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
}

export function ProductListSkeleton({ rowCount = ROW_COUNT }: { rowCount?: number }) {
  return (
    <div className="w-full">
      <TableHeader />
      <div className="pr-4">
        {Array.from({ length: rowCount }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    </div>
  );
}

export { ROW_HEIGHT };
