// Apify webhook receiver. Accepts either:
//  - the run-completion payload we register in startActorRun: {runId, datasetId, status}
//  - a raw batch push: {platform, items: [...]} (e.g. from an Apify integration or a backfill script)
import { NextResponse, type NextRequest } from "next/server";
import { timingSafeEqual } from "node:crypto";
import { ACTORS, normalize, type Platform } from "@/lib/apify";
import { env } from "@/lib/env";
import { ingestRecords } from "@/lib/pipeline/ingest";
import { inngest } from "@/inngest/client";

export const runtime = "nodejs";

function authorized(req: NextRequest): boolean {
  const expected = env.apifyWebhookSecret();
  if (!expected) return process.env.NODE_ENV !== "production";
  const got = req.headers.get("x-webhook-secret") ?? "";
  return got.length === expected.length && timingSafeEqual(Buffer.from(got), Buffer.from(expected));
}

export async function POST(req: NextRequest) {
  if (!authorized(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  const body = (await req.json()) as { platform?: Platform; datasetId?: string; runId?: string; status?: string; items?: unknown[] };
  const platform = (req.nextUrl.searchParams.get("platform") ?? body.platform) as Platform | null;
  if (!platform || !(platform in ACTORS)) return NextResponse.json({ error: "unknown platform" }, { status: 400 });

  if (Array.isArray(body.items)) {
    const result = await ingestRecords(normalize(platform, body.items));
    if (result.toProcess.length) {
      await inngest.send(result.toProcess.map((videoId) => ({ name: "video/process.requested" as const, data: { videoId } })));
    }
    return NextResponse.json(result);
  }

  if (!body.datasetId) return NextResponse.json({ error: "datasetId or items required" }, { status: 400 });
  if (body.status && body.status !== "SUCCEEDED") return NextResponse.json({ skipped: body.status });
  await inngest.send({ name: "apify/dataset.ready", data: { platform, datasetId: body.datasetId, runId: body.runId ?? "" } });
  return NextResponse.json({ queued: body.datasetId }, { status: 202 });
}
