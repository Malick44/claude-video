import { EventSchemas, Inngest } from "inngest";

type Events = {
  "apify/dataset.ready": { data: { platform: "tiktok" | "instagram" | "youtube"; datasetId: string; runId: string } };
  "video/process.requested": { data: { videoId: string } };
  "ingest/run.requested": { data: { platform?: "tiktok" | "instagram" | "youtube" } };
  "digest/generate.requested": { data: { weekStart?: string } };
};

export const inngest = new Inngest({ id: "competitor-intel", schemas: new EventSchemas().fromRecord<Events>() });
