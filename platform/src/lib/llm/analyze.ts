// Multimodal decomposition: transcript (with timestamps) + hook frames + scene
// frames -> strict JSON via structured outputs.
import { readFile } from "node:fs/promises";
import type Anthropic from "@anthropic-ai/sdk";
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import type { Keyframe } from "../media/frames";
import type { Transcript } from "../media/transcribe";
import { fmtTs, timestampedLines } from "../pacing";
import { VideoIntelligenceSchema, type VideoIntelligence } from "../schema";
import { anthropic, baseParams } from "./client";

const SYSTEM = `You are a short-form video strategist decomposing competitor TikToks, Reels and Shorts.
Short-form retention is driven as much by what is on screen (text overlays, b-roll, cuts, gestures) as by what is said, so read the frames as carefully as the transcript.
Rules:
- Quote hooks and overlay text verbatim. Never invent speech that is not in the transcript; if there is no speech, say so and rely on the frames.
- Beats must tile the whole video in order, using the transcript timestamps.
- Pick the single closest archetype / beat type / CTA type from the allowed values.
- Use the provided measured pacing for pacing_words_per_minute.
- Remix takeaways must be transferable mechanisms, not topic copies.`;

export interface AnalyzeInput {
  platform: string;
  handle: string;
  caption: string | null;
  durationSeconds: number | null;
  metrics: { views: number; outlierMultiplier: number | null; engagementRate: number | null };
  transcript: Transcript;
  frames: Keyframe[];
  measured: { wpm: number | null; cutsPerMinute: number | null; sceneCuts: number };
}

export async function analyzeVideo(input: AnalyzeInput): Promise<{ analysis: VideoIntelligence; model: string }> {
  const content: Anthropic.Beta.BetaContentBlockParam[] = [];
  for (const f of input.frames) {
    content.push({ type: "text", text: `Frame @ ${f.t.toFixed(1)}s (${f.kind === "hook" ? "hook window" : "scene cut"})` });
    content.push({
      type: "image",
      source: { type: "base64", media_type: "image/jpeg", data: (await readFile(f.path)).toString("base64") },
    });
  }

  const lines = timestampedLines(input.transcript.words);
  const sentiment = input.transcript.sentimentSegments
    .filter((s) => s.sentiment !== "neutral")
    .map((s) => `[${fmtTs(s.start)}-${fmtTs(s.end)}] ${s.sentiment}: ${s.text}`);

  content.push({
    type: "text",
    text: [
      `<video platform="${input.platform}" creator="@${input.handle}" duration_seconds="${input.durationSeconds ?? "unknown"}">`,
      `<caption>${input.caption ?? ""}</caption>`,
      `<performance views="${input.metrics.views}" outlier_multiplier="${input.metrics.outlierMultiplier ?? "n/a"}" engagement_rate="${input.metrics.engagementRate ?? "n/a"}" />`,
      `<measured_pacing words_per_minute="${input.measured.wpm ?? "n/a"}" scene_cuts="${input.measured.sceneCuts}" cuts_per_minute="${input.measured.cutsPerMinute ?? "n/a"}" />`,
      `<transcript>\n${lines.length ? lines.join("\n") : "(no speech detected)"}\n</transcript>`,
      sentiment.length ? `<sentiment_shifts>\n${sentiment.join("\n")}\n</sentiment_shifts>` : "",
      `</video>`,
      "Decompose this video.",
    ].join("\n"),
  });

  const response = await anthropic().beta.messages.parse({
    ...baseParams(),
    max_tokens: 16000,
    system: SYSTEM,
    messages: [{ role: "user", content }],
    output_config: { format: betaZodOutputFormat(VideoIntelligenceSchema) },
  });

  if (response.stop_reason === "refusal") throw new Error("Analysis declined by model");
  if (!response.parsed_output) throw new Error(`Analysis returned no parseable output (stop_reason=${response.stop_reason})`);

  const analysis = response.parsed_output;
  if (input.measured.wpm != null) analysis.structural_metrics.pacing_words_per_minute = input.measured.wpm;
  return { analysis, model: response.model };
}
