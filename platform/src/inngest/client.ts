import { EventSchemas, Inngest } from "inngest";
import type { Platform } from "@/lib/apify";

type Events = {
  "apify/dataset.ready": { data: { platform: Platform; datasetId: string; runId: string } };
  "video/process.requested": { data: { videoId: string } };
  "ingest/run.requested": { data: { platform?: Platform } };
  "digest/generate.requested": { data: { weekStart?: string } };
};

export const inngest = new Inngest({ id: "competitor-intel", schemas: new EventSchemas().fromRecord<Events>() });
