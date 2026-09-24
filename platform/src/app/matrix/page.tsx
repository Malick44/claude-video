import Link from "next/link";
import { db } from "@/lib/db";
import { compact, multiplier, PLATFORM_LABEL } from "@/lib/format";

export const dynamic = "force-dynamic";

interface Cell {
  hook_archetype: string; platform: string; video_count: number; avg_multiplier: number | null;
  median_multiplier: number | null; avg_views: number | null; avg_engagement_rate: number | null; outlier_count: number;
}

const WINDOWS = { "7": "This week", "30": "30 days", "90": "90 days" } as const;
const PLATFORMS = ["tiktok", "instagram", "youtube"];

/** Sequential shading by median multiplier: 1× = neutral, ≥4× = full. */
function shade(m: number | null): string {
  if (m == null) return "transparent";
  const t = Math.max(0, Math.min(1, (m - 0.5) / 3.5));
  return `rgba(16, 185, 129, ${0.08 + t * 0.62})`;
}

export default async function MatrixPage({ searchParams }: { searchParams: Promise<{ days?: string }> }) {
  const { days = "7" } = await searchParams;
  const since = new Date(Date.now() - Number(days) * 86_400_000).toISOString();
  const { data, error } = await db().rpc("archetype_matrix", { p_since: since });
  const cells = (data ?? []) as Cell[];

  // Roll up across platforms for the "All" column + ranking.
  const byArchetype = new Map<string, { cells: Record<string, Cell>; n: number; weighted: number; outliers: number; views: number }>();
  for (const c of cells) {
    const agg = byArchetype.get(c.hook_archetype) ?? { cells: {}, n: 0, weighted: 0, outliers: 0, views: 0 };
    agg.cells[c.platform] = c;
    agg.n += Number(c.video_count);
    agg.weighted += Number(c.avg_multiplier ?? 0) * Number(c.video_count);
    agg.outliers += Number(c.outlier_count);
    agg.views += Number(c.avg_views ?? 0) * Number(c.video_count);
    byArchetype.set(c.hook_archetype, agg);
  }
  const rows = [...byArchetype.entries()]
    .map(([archetype, a]) => ({ archetype, ...a, avg: a.n ? a.weighted / a.n : null, avgViews: a.n ? a.views / a.n : null }))
    .sort((x, y) => (y.avg ?? 0) - (x.avg ?? 0));
  const top = rows[0];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Hook &amp; Pattern Matrix</h1>
          <p className="text-sm text-zinc-400">Which hook archetypes beat their creator&apos;s baseline? Platform cells show the median outlier multiplier; “All platforms” is the video-weighted mean (n videos).</p>
        </div>
        <div className="flex gap-1 rounded-md border border-zinc-700 p-0.5 text-sm">
          {Object.entries(WINDOWS).map(([d, label]) => (
            <Link key={d} href={`/matrix?days=${d}`} className={`rounded px-3 py-1 ${d === days ? "bg-zinc-700 text-white" : "text-zinc-400"}`}>{label}</Link>
          ))}
        </div>
      </div>

      {error && <p className="text-red-400">{error.message}</p>}
      {top && (
        <div className="rounded-lg border border-emerald-900 bg-emerald-950/30 p-4 text-sm">
          <span className="text-zinc-400">Top performer:</span>{" "}
          <span className="font-semibold text-emerald-300">{top.archetype}</span> — {multiplier(top.avg)} the median view baseline across {top.n} videos ({top.outliers} viral outliers).
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-left text-xs uppercase tracking-wide text-zinc-400">
            <tr>
              <th className="px-3 py-2">Hook archetype</th>
              <th className="px-3 py-2 text-right">All platforms</th>
              {PLATFORMS.map((p) => <th key={p} className="px-3 py-2 text-right">{PLATFORM_LABEL[p]}</th>)}
              <th className="px-3 py-2 text-right">Avg views</th>
              <th className="px-3 py-2 text-right">Outliers</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.archetype} className="border-t border-zinc-800">
                <td className="px-3 py-2 font-medium">
                  <Link href={`/?window=${days === "7" ? "7d" : days === "30" ? "30d" : "90d"}`} className="hover:underline">{r.archetype}</Link>
                </td>
                <td className="px-3 py-2 text-right font-semibold tabular-nums" style={{ background: shade(r.avg) }}>
                  {multiplier(r.avg)} <span className="font-normal text-zinc-400">({r.n})</span>
                </td>
                {PLATFORMS.map((p) => {
                  const c = r.cells[p];
                  return (
                    <td key={p} className="px-3 py-2 text-right tabular-nums" style={{ background: shade(c?.median_multiplier ?? null) }}>
                      {c ? <>{multiplier(c.median_multiplier)} <span className="text-zinc-400">({c.video_count})</span></> : <span className="text-zinc-600">—</span>}
                    </td>
                  );
                })}
                <td className="px-3 py-2 text-right tabular-nums text-zinc-300">{compact(r.avgViews)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{r.outliers}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={7} className="px-3 py-10 text-center text-zinc-500">No analyzed videos in this window yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
