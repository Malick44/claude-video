import { ACTORS, fetchDataset, normalize, startActorRun, type Platform } from "@/lib/apify";
import { db, must } from "@/lib/db";
import { weeklyDigest } from "@/lib/llm/digest";
import { ingestRecords } from "@/lib/pipeline/ingest";
import { enrichVideo, loadVideo, setStatus, storeIntelligence } from "@/lib/pipeline/process";
import { inngest } from "./client";

const PLATFORMS = Object.keys(ACTORS) as Platform[];
const HANDLES_PER_RUN = 25;

/** Phase 1: scheduled incremental pulls (every 6h). Apify calls back via webhook. */
export const scheduleIngest = inngest.createFunction(
  { id: "schedule-ingest" },
  [{ cron: process.env.INGEST_CRON ?? "0 */6 * * *" }, { event: "ingest/run.requested" }],
  async ({ event, step }) => {
    const only = (event?.data as { platform?: Platform } | undefined)?.platform;
    const runs: string[] = [];
    for (const platform of only ? [only] : PLATFORMS) {
      const handles = await step.run(`handles-${platform}`, async () => {
        const rows = must(
          await db().from("competitors").select("handle").eq("platform", platform).eq("active", true),
          "list competitors",
        ) as { handle: string }[];
        return rows.map((r) => r.handle);
      });
      for (let i = 0; i < handles.length; i += HANDLES_PER_RUN) {
        const batch = handles.slice(i, i + HANDLES_PER_RUN);
        const { runId } = await step.run(`start-${platform}-${i}`, () => startActorRun(platform, batch));
        runs.push(runId);
      }
    }
    return { runs };
  },
);

/** Webhook payload -> normalize -> upsert -> rescore -> fan out processing. */
export const ingestDataset = inngest.createFunction(
  { id: "ingest-dataset", concurrency: { limit: 2 }, retries: 3 },
  { event: "apify/dataset.ready" },
  async ({ event, step }) => {
    const result = await step.run("ingest", async () => {
      const items = await fetchDataset(event.data.datasetId);
      return ingestRecords(normalize(event.data.platform, items));
    });
    if (result.toProcess.length) {
      await step.sendEvent(
        "fan-out",
        result.toProcess.map((videoId) => ({ name: "video/process.requested" as const, data: { videoId } })),
      );
    }
    return result;
  },
);

/** Phase 2: media + transcription + multimodal analysis + embeddings. */
export const processVideo = inngest.createFunction(
  {
    id: "process-video",
    concurrency: { limit: Number(process.env.PROCESS_CONCURRENCY ?? 4) },
    throttle: { limit: 30, period: "1m" },
    retries: 2,
    onFailure: async ({ event, error }) => {
      await setStatus(event.data.event.data.videoId, "failed", error.message.slice(0, 2000));
    },
  },
  { event: "video/process.requested" },
  async ({ event, step }) => {
    const { videoId } = event.data;
    await step.run("mark-processing", () => setStatus(videoId, "processing"));
    const enriched = await step.run("enrich", async () => enrichVideo(await loadVideo(videoId)));
    await step.run("store", () => storeIntelligence(videoId, enriched.analysis, enriched.model, enriched.transcript.text));
    await step.run("mark-done", () => setStatus(videoId, "done"));
    return { videoId, archetype: enriched.analysis.hook_analysis.hook_archetype };
  },
);

/** Phase 4: Monday digest summarizing format trends across tracked accounts. */
export const generateDigest = inngest.createFunction(
  { id: "weekly-digest" },
  [{ cron: "0 8 * * 1" }, { event: "digest/generate.requested" }],
  async ({ step }) => {
    const weekStart = new Date(Date.now() - 7 * 86_400_000).toISOString().slice(0, 10);
    const data = await step.run("gather", async () => {
      const sb = db();
      const outliers = must(
        await sb
          .from("outlier_feed")
          .select("id, platform, handle, caption, views, outlier_multiplier, engagement_rate, hook_text, hook_archetype, cta_type, primary_topic_cluster, pacing_wpm")
          .gte("published_at", weekStart)
          .eq("is_outlier", true)
          .order("outlier_multiplier", { ascending: false })
          .limit(40),
        "outliers",
      );
      const matrix = must(await sb.rpc("archetype_matrix", { p_since: weekStart }), "matrix");
      const prev = await sb.from("weekly_digests").select("digest_json").order("week_start", { ascending: false }).limit(1).maybeSingle();
      return { outliers, matrix, previous: prev.data?.digest_json ?? null };
    });
    const digest = await step.run("synthesize", () =>
      weeklyDigest({ weekStart, outliers: data.outliers as unknown[], matrix: data.matrix as unknown[], previousDigest: data.previous }),
    );
    await step.run("store", async () =>
      must(await db().from("weekly_digests").upsert({ week_start: weekStart, digest_json: digest }, { onConflict: "week_start" }), "store digest"),
    );
    return { weekStart };
  },
);

export const functions = [scheduleIngest, ingestDataset, processVideo, generateDigest];
