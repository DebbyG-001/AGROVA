"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/ui";

const items = [
  { href: "/app", label: "Home" },
  { href: "/app/ai", label: "AI" },
  { href: "/app/livestock", label: "Livestock" },
  { href: "/app/finance", label: "Finance" },
  { href: "/app/alerts", label: "Alerts" },
];

function useActive() {
  const path = usePathname();
  return (href: string) => (href === "/app" ? path === "/app" : path.startsWith(href));
}

/** Phone / tablet: fixed bottom bar. Hidden on desktop (see SideNav). */
export function BottomNav() {
  const isActive = useActive();
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 border-t border-forest/15 bg-forest px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] lg:hidden"
    >
      <ul className="mx-auto grid max-w-xl grid-cols-5">
        {items.map((i) => {
          const active = isActive(i.href);
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

/** Desktop: full-height sidebar. Hidden below the lg breakpoint. */
export function SideNav({ farmName }: { farmName: string }) {
  const isActive = useActive();
  return (
    <aside className="sticky top-0 hidden h-dvh flex-col justify-between bg-forest p-5 text-lime lg:flex">
      <div>
        <Link href="/" aria-label="Agrova home" className="block px-2 pb-8">
          <Logo light />
        </Link>
        <nav aria-label="Primary">
          <ul className="space-y-1">
            {items.map((i) => {
              const active = isActive(i.href);
              return (
                <li key={i.href}>
                  <Link
                    href={i.href}
                    aria-current={active ? "page" : undefined}
                    className={`label flex min-h-11 items-center rounded-full px-4 transition-colors ${
                      active ? "bg-lime text-forest" : "text-lime/80 hover:bg-lime/10"
                    }`}
                  >
                    {i.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
      <div className="rounded-2xl border border-lime/20 p-4">
        <p className="label opacity-70">Farm</p>
        <p className="mt-1 font-bold">{farmName}</p>
      </div>
    </aside>
  );
}
