"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState, useMemo } from "react";
import type { Product, ProductVariant } from "@/lib/types";

export function ProductCard({ product }: { product: Product }) {
  const imageUrls = product.image_urls
    ? product.image_urls.split("|").filter(Boolean)
    : [];
  const [currentIndex, setCurrentIndex] = useState(0);
  const features = product.key_features
    ? product.key_features.split("|").filter(Boolean)
    : [];
  const colorOptions = product.colors
    ? product.colors.split("|").filter(Boolean)
    : [];
  const brandSlug = encodeURIComponent(product.brand);

  const variants: ProductVariant[] = useMemo(() => {
    if (!product.variants?.trim()) return [];
    try {
      const parsed = JSON.parse(product.variants) as ProductVariant[];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [product.variants]);

  const goPrev = () =>
    setCurrentIndex((i) => (i <= 0 ? imageUrls.length - 1 : i - 1));
  const goNext = () =>
    setCurrentIndex((i) => (i >= imageUrls.length - 1 ? 0 : i + 1));
  const hasMultiple = imageUrls.length > 1;

  return (
    <article className="space-y-8 py-6 text-card-foreground">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Carousel column */}
        <div className="flex-1 space-y-4">
          {imageUrls.length > 0 && (
            <div
              className="group/carousel relative w-full"
              role="region"
              aria-roledescription="carousel"
            >
              <div className="relative h-96 w-full overflow-hidden bg-muted">
                <Image
                  key={imageUrls[currentIndex]}
                  src={imageUrls[currentIndex]}
                  alt={`${product.name} – image ${currentIndex + 1} of ${imageUrls.length}`}
                  fill
                  className="object-contain transition-opacity duration-500"
                  unoptimized
                />
              </div>
              {hasMultiple && (
                <>
                  <button
                    type="button"
                    onClick={goPrev}
                    className="absolute left-0 top-1/2 z-10 -translate-y-1/2 rounded-r bg-background/80 p-1.5 text-foreground shadow-sm transition-colors hover:bg-background"
                    aria-label="Previous image"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    onClick={goNext}
                    className="absolute right-0 top-1/2 z-10 -translate-y-1/2 rounded-l bg-background/80 p-1.5 text-foreground shadow-sm transition-colors hover:bg-background"
                    aria-label="Next image"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                  <div className="absolute bottom-2 left-1/2 z-10 flex -translate-x-1/2 gap-1.5">
                    {imageUrls.map((_, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setCurrentIndex(i)}
                        className={`h-2 w-2 rounded-full transition-colors ${
                          i === currentIndex
                            ? "bg-primary"
                            : "bg-muted-foreground/40 hover:bg-muted-foreground/60"
                        }`}
                        aria-label={`Go to image ${i + 1}`}
                        aria-current={i === currentIndex ? "true" : undefined}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Details column */}
        <div className="flex-1 space-y-6">
          <div>
            <Link
              href={`/brand/${brandSlug}`}
              className="text-md font-medium text-primary hover:underline"
            >
              {product.brand}
            </Link>
            {product.category && (
              <span className="text-md text-muted-foreground"> · {product.category}</span>
            )}
            <h1 className="mt-1 line-clamp-2 text-2xl font-medium md:text-3xl">
              {product.name}
            </h1>
            <div className="mt-2 flex flex-wrap items-baseline gap-2">
              {product.compare_at_price && Number(product.compare_at_price) > 0 && (
                <span className="text-md text-muted-foreground line-through">
                  {product.currency} {product.compare_at_price}
                </span>
              )}
              <p className="text-lg font-semibold">
                {product.currency} {product.price}
              </p>
            </div>
          </div>

          {product.description && (
            <div className="flex flex-col gap-2">
              <p className="text-md font-medium text-primary">Description</p>
              <p className="text-md text-primary">{product.description}</p>
            </div>
          )}

          {features.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-md font-medium text-primary">Key Features</p>
              <ul className="ml-4 list-disc text-md text-primary">
                {features.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}

          {colorOptions.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-md font-medium text-primary">Colors</p>
              <div className="flex flex-wrap gap-2">
                {colorOptions.map((c, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center justify-center rounded-sm border border-border bg-secondary px-2 py-0.5 text-xs font-normal text-secondary-foreground"
                  >
                    {c.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {product.video_url && (
            <div className="flex flex-col gap-2">
              <p className="text-md font-medium text-primary">Video</p>
              <a
                href={product.video_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-md text-primary hover:underline"
              >
                Watch video
              </a>
            </div>
          )}

          {variants.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-md font-medium text-primary">Variants</p>
              <div className="space-y-4">
                {variants.map((v, vi) => (
                  <div key={vi} className="flex flex-col gap-1.5">
                    <span className="text-sm font-medium text-secondary-foreground">
                      {v.title}
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {v.options.map((opt, oi) => (
                        <span
                          key={oi}
                          className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 text-xs ${
                            opt.available
                              ? "border-border bg-secondary text-secondary-foreground"
                              : "border-muted bg-muted text-muted-foreground"
                          }`}
                        >
                          {opt.value}
                          {opt.available === false && (
                            <span className="text-muted-foreground">(unavailable)</span>
                          )}
                          {opt.price != null && opt.price > 0 && (
                            <span className="font-medium">
                              {product.currency} {opt.price}
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
