import Anthropic from "@anthropic-ai/sdk";
import { env } from "../env";

let client: Anthropic | null = null;
export function anthropic(): Anthropic {
  client ??= new Anthropic();
  return client;
}

/**
 * Shared request options. Server-side refusal fallbacks are on by default so a
 * declined request is retried on a fallback model inside the same call.
 */
export function baseParams() {
  return {
    model: env.analysisModel(),
    thinking: { type: "adaptive" as const },
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default" as const,
  };
}
