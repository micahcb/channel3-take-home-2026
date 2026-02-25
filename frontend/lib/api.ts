/** Base URL for the FastAPI backend. Set NEXT_PUBLIC_API_URL in .env (e.g. http://localhost:8000). */
export const API_BASE_URL =
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

export function productsUrl(brand?: string): string {
  const url = `${API_BASE_URL}/api/products`;
  if (brand) return `${url}?brand=${encodeURIComponent(brand)}`;
  return url;
}

export function productBySlugUrl(slug: string): string {
  return `${API_BASE_URL}/api/products/${encodeURIComponent(slug)}`;
}
