import { RemixStudio } from "@/components/RemixStudio";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export default async function RemixPage({ searchParams }: { searchParams: Promise<{ video?: string }> }) {
  const { video } = await searchParams;
  const sb = db();
  const [candidates, brands] = await Promise.all([
    sb.from("outlier_feed").select("id, handle, platform, hook_text, hook_archetype, outlier_multiplier, thumbnail_url")
      .not("hook_archetype", "is", null).order("outlier_multiplier", { ascending: false, nullsFirst: false }).limit(100),
    sb.from("brand_profiles").select("id, name, context").order("created_at"),
  ]);
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Remix Studio</h1>
        <p className="text-sm text-zinc-400">Adapt a proven outlier&apos;s mechanism — hook archetype, beat timings, pacing — into three scripts for your brand.</p>
      </div>
      <RemixStudio videos={candidates.data ?? []} brands={brands.data ?? []} initialVideoId={video ?? null} />
    </div>
  );
}
