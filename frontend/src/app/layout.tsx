import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Onest } from "next/font/google";
import "./globals.css";

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const onest = Onest({
  variable: "--font-onest",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Agrova — Your AI Farm Companion",
  description:
    "Agrova turns everyday farm conversations into intelligent records, insights, health guidance and early warnings.",
};

export const viewport: Viewport = {
  themeColor: "#07260d",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${plexMono.variable} ${onest.variable}`}>
      <body className="min-h-dvh">{children}</body>
    </html>
  );
}
