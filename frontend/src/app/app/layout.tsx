import Link from "next/link";
import { Logo } from "@/components/ui";
import { BottomNav } from "@/components/bottom-nav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex min-h-dvh max-w-3xl flex-col bg-paper">
      <header className="flex items-center justify-between bg-lime px-5 py-3">
        <Link href="/" aria-label="Agrova home">
          <Logo />
        </Link>
        <span className="label">Dons Farm</span>
      </header>
      <main className="flex-1 px-4 pt-5 pb-28">{children}</main>
      <BottomNav />
    </div>
  );
}
