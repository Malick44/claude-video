import { OutlierFeed } from "@/components/OutlierFeed";
import { db } from "@/lib/db";
import type { FeedRow } from "@/lib/types";

export const dynamic = "force-dynamic";

const WINDOWS: Record<string, number | null> = { "7d": 7, "30d": 30, "90d": 90, all: null };

export default async function FeedPage({ searchParams }: { searchParams: Promise<{ window?: string }> }) {
  const { window = "30d" } = await searchParams;
  const days = Object.prototype.hasOwnProperty.call(WINDOWS, window) ? WINDOWS[window] : WINDOWS["30d"];
  let q = db().from("outlier_feed").select("*").order("outlier_multiplier", { ascending: false, nullsFirst: false }).limit(1000);
  if (days) q = q.gte("published_at", new Date(Date.now() - days * 86_400_000).toISOString());
  const { data, error } = await q;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Outlier Feed</h1>
        <p className="text-sm text-zinc-400">
          Ranked by outlier multiplier — views ÷ the creator&apos;s median over their last 20 videos — not raw views.
        </p>
      </div>
      {error ? (
        <p className="rounded-md border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">Failed to load feed: {error.message}</p>
      ) : (
        <OutlierFeed rows={(data ?? []) as FeedRow[]} window={window} windows={Object.keys(WINDOWS)} />
      )}
    </div>
  );
}
