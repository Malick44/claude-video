// Weekly rollup: what formats are rising across tracked accounts.
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { DigestSchema, type Digest } from "../schema";
import { anthropic, baseParams } from "./client";

export async function weeklyDigest(input: { weekStart: string; outliers: unknown[]; matrix: unknown[]; previousDigest?: unknown }): Promise<Digest> {
  const response = await anthropic().beta.messages.parse({
    ...baseParams(),
    max_tokens: 16000,
    system: "You are a content-intelligence analyst writing a weekly brief for a video content team. Be specific and cite video ids as evidence.",
    messages: [
      {
        role: "user",
        content: `<week_start>${input.weekStart}</week_start>
<archetype_matrix>${JSON.stringify(input.matrix)}</archetype_matrix>
<outliers_this_week>${JSON.stringify(input.outliers)}</outliers_this_week>
${input.previousDigest ? `<last_week_digest>${JSON.stringify(input.previousDigest)}</last_week_digest>` : ""}
Summarize new and rising format trends, the best hooks, what is fading versus last week, and concrete experiments for our team to run next week.`,
      },
    ],
    output_config: { format: betaZodOutputFormat(DigestSchema) },
  });
  if (!response.parsed_output) throw new Error(`Digest returned no output (stop_reason=${response.stop_reason})`);
  return response.parsed_output;
}
