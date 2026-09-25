// Remix Studio: adapt an outlier's mechanism to the user's brand, keeping its
// beat timings and pacing.
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { beatWordBudgets } from "../pacing";
import { RemixSchema, type Remix, type VideoIntelligence } from "../schema";
import { anthropic, baseParams } from "./client";

export async function remixScripts(opts: {
  brandContext: string;
  analysis: VideoIntelligence;
  transcript: string | null;
  variants?: number;
  extraDirection?: string;
}): Promise<{ remix: Remix; model: string }> {
  const { analysis } = opts;
  const variants = opts.variants ?? 3;
  const wpm = analysis.structural_metrics.pacing_words_per_minute || 160;
  const budgets = beatWordBudgets(analysis.narrative_beats, wpm);
  const beatPlan = analysis.narrative_beats
    .map((b, i) => `${b.timestamp_range} | ${b.beat_type} | ~${budgets[i]} words | original: ${b.summary}${b.on_screen_text ? ` | overlay: "${b.on_screen_text}"` : ""}`)
    .join("\n");

  const prompt = `<brand_context>
${opts.brandContext}
</brand_context>

<outlier_breakdown>
${JSON.stringify(analysis, null, 2)}
</outlier_breakdown>

<original_transcript>
${opts.transcript ?? "(none)"}
</original_transcript>

<beat_plan wpm="${wpm}">
${beatPlan}
</beat_plan>

Write ${variants} distinct scripts for the brand that reuse this outlier's *mechanism* (hook archetype, retention trigger, beat structure, CTA style, loop) — not its topic or wording.
Each script must keep the exact beat timestamp ranges and beat types from the beat plan, and each beat's voiceover should land within ~15% of that beat's word budget so the pacing matches.
Make the three variants genuinely different angles. Only use claims supported by the brand context.${opts.extraDirection ? `\n\nAdditional direction: ${opts.extraDirection}` : ""}`;

  const stream = anthropic().beta.messages.stream({
    ...baseParams(),
    max_tokens: 32000,
    system: "You are a senior video scriptwriter. You adapt proven formats to new brands without plagiarising them.",
    messages: [{ role: "user", content: prompt }],
    output_config: { format: betaZodOutputFormat(RemixSchema) },
  });
  const message = await stream.finalMessage();
  if (message.stop_reason === "refusal") throw new Error("Remix declined by model");
  const text = message.content.flatMap((b) => (b.type === "text" ? [b.text] : [])).join("");
  return { remix: RemixSchema.parse(JSON.parse(text)), model: message.model };
}
