"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/app", label: "Home" },
  { href: "/app/ai", label: "AI" },
  { href: "/app/livestock", label: "Livestock" },
  { href: "/app/finance", label: "Finance" },
  { href: "/app/alerts", label: "Alerts" },
];

export function BottomNav() {
  const path = usePathname();
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 mx-auto max-w-3xl border-t border-forest/15 bg-forest px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]"
    >
      <ul className="grid grid-cols-5">
        {items.map((i) => {
          const active = i.href === "/app" ? path === "/app" : path.startsWith(i.href);
          return (
            <li key={i.href}>
              <Link
                href={i.href}
                aria-current={active ? "page" : undefined}
                className={`label flex min-h-12 items-center justify-center rounded-full text-[0.7rem] ${
                  active ? "bg-lime text-forest" : "text-lime/80"
                }`}
              >
                {i.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
