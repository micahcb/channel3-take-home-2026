"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function NavSegments() {
  const pathname = usePathname();

  const segments: { label: string; href: string | null }[] = [
    { label: "Dashboard", href: "/" },
  ];

  // This should be extrapolated in the future to ensure a simpler structure based on defined naming conventions

  if (pathname.startsWith("/product/")) {
    segments.push({ label: "Product", href: null });
  } else if (pathname.startsWith("/brand/")) {
    const slug = pathname.replace(/^\/brand\//, "").split("/")[0];
    segments.push({
      label: slug ? decodeURIComponent(slug) : "Brand",
      href: null,
    });
  }

  return (
    <div className="flex items-center gap-2 text-md font-medium text-white/90">
      {segments.map((seg, i) => (
        <span key={i} className="flex items-center gap-2">
          {i > 0 && <span className="text-white/50">|</span>}
          {seg.href ? (
            <Link
              href={seg.href}
              className="transition-colors hover:text-white"
            >
              {seg.label}
            </Link>
          ) : (
            <span className="text-white">{seg.label}</span>
          )}
        </span>
      ))}
    </div>
  );
}

export function Navbar() {
  return (
    <nav className="flex h-[56px] w-full items-center justify-between border-b border-white/10 px-4">
      <NavSegments />
    </nav>
  );
}
