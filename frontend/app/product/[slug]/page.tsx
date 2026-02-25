"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { ProductCardSkeleton } from "@/components/ProductCardSkeleton";
import { productBySlugUrl } from "@/lib/api";
import type { Product } from "@/lib/types";

export default function ProductPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    fetch(productBySlugUrl(slug))
      .then((res) => {
        if (res.status === 404) throw new Error("Product not found");
        if (!res.ok) throw new Error("Failed to load product");
        return res.json();
      })
      .then((data) => {
        setProduct(data.product ?? null);
      })
      .catch((err) => {
        setError(err.message ?? "Something went wrong");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background font-sans">
        <main className="mx-auto max-w-5xl px-4 py-12">
          <Link href="/" className="mb-6 inline-block text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
            ← Back to products
          </Link>
          <ProductCardSkeleton />
        </main>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-background font-sans">
        <main className="mx-auto max-w-5xl px-4 py-12">
          <p className="text-destructive">{error ?? "Product not found."}</p>
          <Link href="/" className="mt-4 inline-block text-primary underline-offset-4 hover:underline">
            Back to products
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background font-sans">
      <main className="mx-auto max-w-5xl px-4 py-12">
        <Link href="/" className="mb-6 inline-block text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
          ← Back to products
        </Link>
        <ProductCard product={product} />
      </main>
    </div>
  );
}
