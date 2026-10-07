import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

type ButtonProps = {
  href?: string;
  variant?: "lime" | "forest" | "outline" | "outlineLight";
  children: ReactNode;
  className?: string;
} & Omit<ComponentProps<"button">, "className">;

const variants = {
  lime: "bg-lime text-forest border-forest hover:bg-lime-2",
  forest: "bg-forest text-lime border-forest hover:bg-forest-2",
  outline: "bg-transparent text-forest border-forest hover:bg-forest/5",
  /** For use on dark / video backgrounds */
  outlineLight: "bg-transparent text-lime border-lime hover:bg-lime/10",
};

/** Pill button — the one button style used across landing + app. */
export function Button({
  href,
  variant = "lime",
  children,
  className = "",
  ...rest
}: ButtonProps) {
  const cls = `label inline-flex min-h-11 items-center justify-center gap-2 rounded-full border px-5 py-2 transition-colors ${variants[variant]} ${className}`;
  if (href) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button className={cls} {...rest}>
      {children}
    </button>
  );
}

/** Bracketed mono tag, e.g. [01] or [WE ARE AGROVA,] */
export function Tag({ children }: { children: ReactNode }) {
  return <span className="label">[{children}]</span>;
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl border border-forest/10 bg-white p-4 ${className}`}>
      {children}
    </div>
  );
}

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <span
      className={`label inline-flex items-center gap-2 font-semibold ${light ? "text-lime" : "text-forest"}`}
    >
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
        <path d="M2 16V8l7-6 7 6v8" fill="none" stroke="currentColor" strokeWidth="2" />
        <circle cx="9" cy="11" r="2.2" fill="currentColor" />
      </svg>
      AGROVA
    </span>
  );
}
