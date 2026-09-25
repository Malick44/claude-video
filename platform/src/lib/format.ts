export const compact = (n: number | null | undefined) =>
  n == null ? "—" : new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export const multiplier = (n: number | null | undefined) =>
  n == null ? "—" : `${Number(n).toFixed(n < 0.1 ? 2 : 1)}×`;

export const pct = (n: number | null | undefined) => (n == null ? "—" : `${Number(n).toFixed(1)}%`);

export const shortDate = (s: string | null | undefined) =>
  s ? new Date(s).toLocaleDateString("en", { month: "short", day: "numeric" }) : "—";

/** Tailwind classes for an outlier-multiplier badge. */
export function omTone(n: number | null | undefined): string {
  if (n == null) return "bg-zinc-800 text-zinc-400";
  if (n >= 5) return "bg-fuchsia-500/20 text-fuchsia-300 ring-1 ring-fuchsia-500/40";
  if (n >= 2.5) return "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/40";
  if (n >= 1) return "bg-sky-500/15 text-sky-300";
  return "bg-zinc-800 text-zinc-400";
}

export const PLATFORM_LABEL: Record<string, string> = {
  tiktok: "TikTok",
  instagram: "Instagram Reels",
  youtube: "YouTube Shorts",
  youtube_long: "YouTube Long",
};
