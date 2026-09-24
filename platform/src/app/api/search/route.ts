import { NextResponse } from "next/server";
import { db, must } from "@/lib/db";
import { embed, toVector } from "@/lib/embeddings";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { query, platform, limit } = (await req.json()) as { query?: string; platform?: string; limit?: number };
  if (!query?.trim()) return NextResponse.json({ error: "query required" }, { status: 400 });
  const [vec] = await embed([query]);
  const sb = db();
  const matches = must(
    await sb.rpc("match_videos", { query_embedding: toVector(vec), match_count: Math.min(limit ?? 30, 100), p_platform: platform || null }),
    "match",
  ) as { video_id: string; similarity: number }[];
  if (!matches.length) return NextResponse.json({ results: [] });
  const rows = must(await sb.from("outlier_feed").select("*").in("id", matches.map((m) => m.video_id)), "feed") as { id: string }[];
  const byId = new Map(rows.map((r) => [r.id, r]));
  return NextResponse.json({
    results: matches.flatMap((m) => (byId.has(m.video_id) ? [{ ...byId.get(m.video_id), similarity: m.similarity }] : [])),
  });
}
