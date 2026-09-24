import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const runtime = "nodejs";

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const sb = db();
  const [video, intel, snapshots, similar] = await Promise.all([
    sb.from("competitor_videos").select("*, competitors(handle, platform, follower_count, median_views_last_20)").eq("id", id).single(),
    sb.from("video_intelligence").select("*").eq("video_id", id).maybeSingle(),
    sb.from("video_metric_snapshots").select("captured_at, age_bucket, views, likes, comments, shares, saves").eq("video_id", id).order("captured_at"),
    sb.rpc("similar_hooks", { p_video_id: id, match_count: 6 }),
  ]);
  if (video.error) return NextResponse.json({ error: video.error.message }, { status: 404 });
  const { hook_embedding: _h, content_embedding: _c, ...intelligence } = intel.data ?? {};
  return NextResponse.json({
    video: video.data,
    intelligence: intel.data ? intelligence : null,
    snapshots: snapshots.data ?? [],
    similar: similar.data ?? [],
  });
}
