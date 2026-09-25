import { NextResponse } from "next/server";
import { ACTORS, type Platform } from "@/lib/apify";
import { inngest } from "@/inngest/client";

export async function POST(req: Request) {
  const { platform, videoId } = (await req.json().catch(() => ({}))) as { platform?: Platform; videoId?: string };
  if (!videoId && platform !== undefined && (typeof platform !== "string" || !(platform in ACTORS))) {
    return NextResponse.json({ error: "unknown platform" }, { status: 400 });
  }
  if (videoId) await inngest.send({ name: "video/process.requested", data: { videoId } });
  else await inngest.send({ name: "ingest/run.requested", data: { platform } });
  return NextResponse.json({ queued: true }, { status: 202 });
}
