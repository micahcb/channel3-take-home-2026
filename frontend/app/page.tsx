"use client";

import { useEffect, useState } from "react";
import { ProductListSkeleton } from "@/components/ProductListSkeleton";
import { VirtualizedProductList } from "@/components/VirtualizedProductList";
import { productsUrl } from "@/lib/api";
import type { Product } from "@/lib/types";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [listHeight, setListHeight] = useState(600);

  useEffect(() => {
    const updateHeight = () =>
      setListHeight(Math.max(400, window.innerHeight - 240));
    const id = requestAnimationFrame(updateHeight);
    window.addEventListener("resize", updateHeight);
    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener("resize", updateHeight);
    };
  }, []);

  useEffect(() => {
    fetch(productsUrl())
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load products");
        return res.json();
      })
      .then((data) => {
        setProducts(data.products ?? []);
      })
      .catch((err) => {
        setError(err.message ?? "Something went wrong");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-background font-sans">
      <main className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="mb-8 text-2xl font-semibold tracking-tight text-foreground">
          Products
        </h1>
        {loading && <ProductListSkeleton />}
        {error && (
          <p className="text-destructive">{error}</p>
        )}
        {!loading && !error && products.length === 0 && (
          <p className="text-muted-foreground">No products found.</p>
        )}
        {!loading && !error && products.length > 0 && (
          <VirtualizedProductList products={products} height={listHeight} />
        )}
      </main>
    </div>
  );
}
