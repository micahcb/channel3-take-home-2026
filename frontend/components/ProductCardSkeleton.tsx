"use client";

import { Skeleton } from "@/components/ui/skeleton";

export function ProductCardSkeleton() {
  return (
    <article className="rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm">
      <div className="flex flex-col gap-6 sm:flex-row">
        <Skeleton className="h-48 w-full shrink-0 rounded-lg sm:h-56 sm:w-56" />
        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div>
            <Skeleton className="mb-2 h-4 w-32" />
            <Skeleton className="h-6 w-[80%] max-w-[280px]" />
            <Skeleton className="mt-2 h-5 w-24" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
          <ul className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[83%]" />
            <Skeleton className="h-4 w-[80%]" />
          </ul>
        </div>
      </div>
    </article>
  );
}
