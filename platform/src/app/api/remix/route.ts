import { NextResponse } from "next/server";
import { db, must } from "@/lib/db";
import { remixScripts } from "@/lib/llm/remix";
import type { VideoIntelligence } from "@/lib/schema";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(req: Request) {
  const body = (await req.json()) as { videoId?: string; brandProfileId?: string; brandContext?: string; direction?: string };
  if (!body.videoId) return NextResponse.json({ error: "videoId required" }, { status: 400 });
  const sb = db();

  let brandContext = body.brandContext?.trim() ?? "";
  if (body.brandProfileId) {
    const brand = must(await sb.from("brand_profiles").select("context").eq("id", body.brandProfileId).single(), "brand") as { context: string };
    brandContext = brandContext || brand.context;
  }
  if (!brandContext) return NextResponse.json({ error: "brand context required" }, { status: 400 });

  const intel = await sb.from("video_intelligence").select("analysis_json").eq("video_id", body.videoId).maybeSingle();
  if (!intel.data?.analysis_json) return NextResponse.json({ error: "video has not been analyzed yet" }, { status: 409 });
  const video = must(await sb.from("competitor_videos").select("raw_transcript").eq("id", body.videoId).single(), "video") as { raw_transcript: string | null };

  const { remix, model } = await remixScripts({
    brandContext,
    analysis: intel.data.analysis_json as VideoIntelligence,
    transcript: video.raw_transcript,
    extraDirection: body.direction,
  });
  const saved = must(
    await sb
      .from("remix_scripts")
      .insert({ video_id: body.videoId, brand_profile_id: body.brandProfileId ?? null, scripts_json: remix, model })
      .select("id")
      .single(),
    "save remix",
  ) as { id: string };
  return NextResponse.json({ id: saved.id, ...remix });
}
