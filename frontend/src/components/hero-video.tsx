"use client";

import { useEffect, useRef, useSyncExternalStore } from "react";

type NetworkInformation = { saveData?: boolean; effectiveType?: string };

function videoAllowed(): boolean {
  const conn = (navigator as Navigator & { connection?: NetworkInformation }).connection;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const slow = conn?.saveData || conn?.effectiveType === "2g" || conn?.effectiveType === "slow-2g";
  return !reduce && !slow;
}

const subscribe = () => () => {};

/**
 * Silent looping hero background.
 * - Skipped (poster only) for reduced-motion, data-saver and slow (2g) connections.
 * - Paused while off-screen to save battery and data.
 * The WebM (~320 KB) is served first; the MP4 is the Safari fallback.
 */
export function HeroVideo({ className = "" }: { className?: string }) {
  const ref = useRef<HTMLVideoElement>(null);
  // false on the server and during hydration, then the real answer on the client
  const allowed = useSyncExternalStore(subscribe, videoAllowed, () => false);

  useEffect(() => {
    const el = ref.current;
    if (!el || !allowed) return;
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) el.play().catch(() => {});
      else el.pause();
    });
    io.observe(el);
    return () => io.disconnect();
  }, [allowed]);

  return (
    <div className={`absolute inset-0 overflow-hidden bg-forest ${className}`} aria-hidden="true">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/video/poster.jpg" alt="" className="absolute inset-0 size-full object-cover" />
      {allowed && (
        <video
          ref={ref}
          className="absolute inset-0 size-full object-cover"
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          poster="/video/poster.jpg"
        >
          <source src="/video/hero.webm" type="video/webm" />
          <source src="/video/hero.mp4" type="video/mp4" />
        </video>
      )}
      {/* Brand tint + legibility for the chat bubbles and stats on top */}
      <div className="absolute inset-0 bg-forest/40" />
      {/* Darker on the text side (left on desktop) so the headline stays readable */}
      <div className="absolute inset-0 bg-gradient-to-r from-forest/80 via-forest/35 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-t from-forest via-forest/20 to-transparent" />
    </div>
  );
}
