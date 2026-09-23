import { AddCompetitor, IngestTrigger, ToggleActive } from "@/components/Triggers";
import { db } from "@/lib/db";
import { compact, PLATFORM_LABEL, shortDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function CompetitorsPage() {
  const { data } = await db()
    .from("competitors")
    .select("id, platform, handle, follower_count, median_views_last_20, niche_category, active, last_scraped_at")
    .order("platform").order("handle");
  const rows = data ?? [];
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tracked Competitors</h1>
          <p className="text-sm text-zinc-400">Scraped every 6h via Apify. Baseline = median views of each creator&apos;s last 20 videos.</p>
        </div>
        <IngestTrigger />
      </div>
      <AddCompetitor />
      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-left text-xs uppercase tracking-wide text-zinc-400">
            <tr><th className="px-3 py-2">Handle</th><th className="px-3 py-2">Platform</th><th className="px-3 py-2">Niche</th>
              <th className="px-3 py-2 text-right">Followers</th><th className="px-3 py-2 text-right">Baseline views</th>
              <th className="px-3 py-2">Last scraped</th><th className="px-3 py-2">Status</th></tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id} className="border-t border-zinc-800">
                <td className="px-3 py-2 font-medium">@{c.handle}</td>
                <td className="px-3 py-2">{PLATFORM_LABEL[c.platform]}</td>
                <td className="px-3 py-2 text-zinc-400">{c.niche_category ?? "—"}</td>
                <td className="px-3 py-2 text-right tabular-nums">{compact(c.follower_count)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{compact(c.median_views_last_20)}</td>
                <td className="px-3 py-2 text-zinc-400">{shortDate(c.last_scraped_at)}</td>
                <td className="px-3 py-2"><ToggleActive id={c.id} active={c.active} /></td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={7} className="px-3 py-10 text-center text-zinc-500">No competitors yet — add one above.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
