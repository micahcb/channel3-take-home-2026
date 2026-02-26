"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { ProductListSkeleton } from "@/components/ProductListSkeleton";
import { VirtualizedProductList } from "@/components/VirtualizedProductList";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { productsUrl } from "@/lib/api";
import type { Product } from "@/lib/types";


// Simple search filter by exact title or brand (will need to be improved, more in README.md writeup)
function filterByExactTitleOrBrand(products: Product[], query: string): Product[] {
  const q = query.trim();
  if (!q) return products;
  const qLower = q.toLowerCase();
  return products.filter(
    (p) =>
      (p.name ?? "").toLowerCase().includes(qLower) ||
      (p.brand ?? "").toLowerCase().includes(qLower)
  );
}

// Home page includes the list of all products in a virtualized list to allow for efficient rendering at scale (will also need pagination)
export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [listHeight, setListHeight] = useState(600);
  const [searchQuery, setSearchQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");

  const handleSearch = useCallback(() => {
    setAppliedQuery(searchQuery);
  }, [searchQuery]);

  const filteredProducts = filterByExactTitleOrBrand(products, appliedQuery);

  // Update the list height based on the window size
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

  // Fetch the products from the FastAPI backend API
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
        <div className="relative mb-6 w-full sm:w-full lg:max-w-sm">
          <div className="relative">
            <Input
              placeholder="Search products..."
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="pr-10"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute inset-y-0 right-0 rounded-l-none text-muted-foreground"
              aria-label="Search"
              onClick={handleSearch}
            >
              <Search className="h-4 w-4" aria-hidden />
            </Button>
          </div>
        </div>
        {/* Skeleton loading state */}
        {loading && <ProductListSkeleton />}
        {/* Error state */}
        {error && (
          <p className="text-destructive">{error}</p>
        )}
        {/* No products found state */}
        {!loading && !error && products.length === 0 && (
          <p className="text-muted-foreground">No products found.</p>
        )}
        {/* No results for search */}
        {!loading && !error && products.length > 0 && filteredProducts.length === 0 && (
          <p className="text-muted-foreground">
            No products match &quot;{appliedQuery}&quot; (by name or brand).
          </p>
        )}
        {/* Products found state */}
        {!loading && !error && filteredProducts.length > 0 && (
          <VirtualizedProductList products={filteredProducts} height={listHeight} />
        )}
      </main>
    </div>
  );
}
