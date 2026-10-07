import Link from "next/link";
import { Logo } from "@/components/ui";
import { BottomNav, SideNav } from "@/components/bottom-nav";
import { farm } from "@/lib/demo-data";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-paper lg:grid lg:grid-cols-[16rem_1fr]">
      <SideNav farmName={farm.name} />
      <div className="flex min-h-dvh min-w-0 flex-col">
        <header className="flex items-center justify-between bg-lime px-5 py-3 lg:hidden">
          <Link href="/" aria-label="Agrova home">
            <Logo />
          </Link>
          <span className="label">{farm.name}</span>
        </header>
        <main className="flex-1 px-4 pt-5 pb-28 md:px-8 lg:px-10 lg:py-8">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}
