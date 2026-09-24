// Centralised env access. Throws lazily so `next build` works without secrets.
function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var ${name}`);
  return v;
}

export const env = {
  supabaseUrl: () => required("SUPABASE_URL"),
  supabaseServiceKey: () => required("SUPABASE_SERVICE_ROLE_KEY"),
  apifyToken: () => required("APIFY_TOKEN"),
  apifyWebhookSecret: () => process.env.APIFY_WEBHOOK_SECRET ?? "",
  deepgramKey: () => required("DEEPGRAM_API_KEY"),
  openaiKey: () => required("OPENAI_API_KEY"),
  analysisModel: () => process.env.ANALYSIS_MODEL ?? "claude-opus-5",
  embeddingModel: () => process.env.EMBEDDING_MODEL ?? "text-embedding-3-small",
  outlierThreshold: () => Number(process.env.OUTLIER_THRESHOLD ?? "2.5"),
  /** Only videos at or above this multiplier get the (expensive) multimodal pass. 0 = analyze everything. */
  analyzeMinMultiplier: () => Number(process.env.ANALYZE_MIN_MULTIPLIER ?? "1.5"),
  appUrl: () => process.env.APP_URL ?? "http://localhost:3000",
};
