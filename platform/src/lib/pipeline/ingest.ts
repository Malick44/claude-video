// Persist a normalized Apify batch: upsert creators + videos, snapshot metrics,
// recompute each touched creator's baseline, and pick videos for deep analysis.
import type { VideoRecord } from "../apify";
import { db, must } from "../db";
import { env } from "../env";
import { refreshBucket } from "../scoring";

export interface IngestResult {
  competitors: number;
  videos: number;
  toProcess: string[]; // competitor_videos.id
}

export async function ingestRecords(records: VideoRecord[]): Promise<IngestResult> {
  if (records.length === 0) return { competitors: 0, videos: 0, toProcess: [] };
  const sb = db();

  // 1. Creators (keep the latest follower count we saw).
  const byCreator = new Map<string, VideoRecord>();
  for (const r of records) byCreator.set(`${r.platform}:${r.handle.toLowerCase()}`, r);
  const competitorRows = must(
    await sb
      .from("competitors")
      .upsert(
        [...byCreator.values()].map((r) => ({
          platform: r.platform,
          handle: r.handle.toLowerCase(),
          ...(r.followerCount != null ? { follower_count: r.followerCount } : {}),
          last_scraped_at: new Date().toISOString(),
        })),
        { onConflict: "platform,handle" },
      )
      .select("id, platform, handle"),
    "upsert competitors",
  ) as { id: string; platform: string; handle: string }[];
  const competitorId = new Map(competitorRows.map((c) => [`${c.platform}:${c.handle}`, c.id]));

  // 2. Which videos are new? (new ones get queued for processing)
  const existing = must(
    await sb
      .from("competitor_videos")
      .select("id, platform, external_video_id, processing_status")
      .in("external_video_id", records.map((r) => r.externalId)),
    "lookup videos",
  ) as { id: string; platform: string; external_video_id: string; processing_status: string }[];
  const known = new Map(existing.map((v) => [`${v.platform}:${v.external_video_id}`, v]));

  // 3. Upsert videos with fresh metrics (media URLs are ephemeral, so refresh them too).
  const videoRows = must(
    await sb
      .from("competitor_videos")
      .upsert(
        records.map((r) => ({
          competitor_id: competitorId.get(`${r.platform}:${r.handle.toLowerCase()}`),
          platform: r.platform,
          external_video_id: r.externalId,
          video_url: r.videoUrl,
          media_url: r.mediaUrl,
          thumbnail_url: r.thumbnailUrl,
          caption: r.caption,
          audio_id: r.audioId,
          duration_seconds: r.durationSeconds,
          published_at: r.publishedAt,
          views: r.views,
          likes: r.likes,
          comments: r.comments,
          shares: r.shares,
          saves: r.saves,
          updated_at: new Date().toISOString(),
        })),
        { onConflict: "platform,external_video_id" },
      )
      .select("id, platform, external_video_id, competitor_id, published_at"),
    "upsert videos",
  ) as { id: string; platform: string; external_video_id: string; competitor_id: string; published_at: string | null }[];

  // 4. Metric snapshots, bucketed by age so we can chart the viral half-life.
  const recByKey = new Map(records.map((r) => [`${r.platform}:${r.externalId}`, r]));
  must(
    await sb.from("video_metric_snapshots").insert(
      videoRows.map((v) => {
        const r = recByKey.get(`${v.platform}:${v.external_video_id}`)!;
        const isNew = !known.has(`${v.platform}:${v.external_video_id}`);
        const bucket = v.published_at ? refreshBucket(new Date(v.published_at)) : null;
        return {
          video_id: v.id,
          age_bucket: isNew ? "ingest" : bucket,
          views: r.views, likes: r.likes, comments: r.comments, shares: r.shares, saves: r.saves,
        };
      }),
    ),
    "insert snapshots",
  );

  // 5. Recompute baselines + rescore (median of last 20 per creator).
  const touched = [...new Set(videoRows.map((v) => v.competitor_id))];
  for (const id of touched) {
    must(
      await sb.rpc("recompute_competitor_baseline", { p_competitor_id: id, p_outlier_threshold: env.outlierThreshold() }),
      "recompute baseline",
    );
  }

  // 6. Queue unprocessed videos that clear the analysis bar (or just became outliers).
  const candidates = must(
    await sb
      .from("competitor_videos")
      .select("id, outlier_multiplier, is_outlier, processing_status")
      .in("id", videoRows.map((v) => v.id))
      .in("processing_status", ["pending", "skipped"]),
    "select candidates",
  ) as { id: string; outlier_multiplier: number | null; is_outlier: boolean; processing_status: string }[];
  const minOm = env.analyzeMinMultiplier();
  const toProcess = candidates
    .filter((c) => c.is_outlier || minOm <= 0 || (c.outlier_multiplier ?? 0) >= minOm)
    .map((c) => c.id);
  const skipped = candidates.filter((c) => !toProcess.includes(c.id) && c.processing_status === "pending").map((c) => c.id);
  if (skipped.length) {
    must(await sb.from("competitor_videos").update({ processing_status: "skipped" }).in("id", skipped), "mark skipped");
  }

  return { competitors: touched.length, videos: videoRows.length, toProcess };
}
