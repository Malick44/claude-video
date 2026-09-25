import { CompetitorTable, type CompetitorItem } from "@/components/CompetitorTable";
import { AddCompetitor, IngestTrigger } from "@/components/Triggers";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export default async function CompetitorsPage() {
  const { data } = await db()
    .from("competitors")
    .select("id, platform, handle, follower_count, median_views_last_20, niche_category, active, last_scraped_at")
    .order("platform").order("handle");
  const rows = (data ?? []) as CompetitorItem[];
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
      <CompetitorTable rows={rows} />
    </div>
  );
}
