// Normalized outlier scoring. Raw views favour big accounts; we score each video
// against its own creator's baseline instead.
//
//   OM = views / median(views of creator's last 20 videos)
//   ER = (likes + 2*comments + 3*saves + 4*shares) / views * 100

export const BASELINE_WINDOW = 20;
export const DEFAULT_OUTLIER_THRESHOLD = 2.5;

export interface Metrics {
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
}

export function median(values: number[]): number | null {
  const xs = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (xs.length === 0) return null;
  const mid = Math.floor(xs.length / 2);
  return xs.length % 2 ? xs[mid] : (xs[mid - 1] + xs[mid]) / 2;
}

/** Median views of the creator's most recent `window` videos (by publish date). */
export function baselineMedian(
  videos: { views: number; publishedAt: Date | string | null }[],
  window = BASELINE_WINDOW,
): number | null {
  const ts = (d: Date | string | null) => (d ? new Date(d).getTime() : -Infinity);
  const recent = [...videos].sort((a, b) => ts(b.publishedAt) - ts(a.publishedAt)).slice(0, window);
  return median(recent.map((v) => v.views));
}

export function outlierMultiplier(views: number, baseline: number | null): number | null {
  if (!baseline || baseline <= 0) return null;
  return round2(views / baseline);
}

export function engagementRate(m: Metrics): number | null {
  if (!m.views || m.views <= 0) return null;
  return round2(((m.likes + 2 * m.comments + 3 * m.saves + 4 * m.shares) / m.views) * 100);
}

export function isOutlier(om: number | null, threshold = DEFAULT_OUTLIER_THRESHOLD): boolean {
  return om !== null && om >= threshold;
}

/** Which metric-refresh bucket a video is due for, given its age. Captures the viral half-life. */
export function refreshBucket(publishedAt: Date, now = new Date()): "d1" | "d3" | "d7" | null {
  const ageDays = (now.getTime() - publishedAt.getTime()) / 86_400_000;
  if (ageDays >= 7 && ageDays < 8) return "d7";
  if (ageDays >= 3 && ageDays < 4) return "d3";
  if (ageDays >= 1 && ageDays < 2) return "d1";
  return null;
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
