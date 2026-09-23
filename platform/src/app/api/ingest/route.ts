import { NextResponse } from "next/server";
import { inngest } from "@/inngest/client";

export async function POST(req: Request) {
  const { platform, videoId } = (await req.json().catch(() => ({}))) as { platform?: "tiktok" | "instagram" | "youtube"; videoId?: string };
  if (videoId) await inngest.send({ name: "video/process.requested", data: { videoId } });
  else await inngest.send({ name: "ingest/run.requested", data: { platform } });
  return NextResponse.json({ queued: true }, { status: 202 });
}
