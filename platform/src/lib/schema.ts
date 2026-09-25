// Structured decomposition schema. Archetypes, beat types and CTA types are
// closed taxonomies so the Pattern Matrix aggregates cleanly across creators.
import { z } from "zod";

export const HOOK_ARCHETYPES = [
  "Negative Contrast / Pattern Interrupt",
  "Contrarian Hot Take",
  "Curiosity Gap",
  "Numbered Promise / Listicle",
  "Result-First / Proof Flash",
  "Direct Audience Callout",
  "Story Open / In Medias Res",
  "Question Hook",
  "How-To Promise",
  "Myth Bust",
  "Challenge / Experiment",
  "Reaction / Stitch",
  "Other",
] as const;

export const BEAT_TYPES = [
  "Hook",
  "Context / Setup",
  "Agitation & Proof",
  "Story",
  "Actionable Pivot",
  "Demonstration",
  "Payoff / Reveal",
  "Call To Action",
  "Loop",
] as const;

export const CTA_TYPES = [
  "Comment Keyword Lead Magnet",
  "Follow for More",
  "Link in Bio",
  "Save / Share Prompt",
  "Product Pitch",
  "Part 2 Tease",
  "Question to Comments",
  "None",
] as const;

export const FrameSceneSchema = z.object({
  timestamp_range: z.string().describe("Scene range in M:SS - M:SS format; no longer than five seconds."),
  figure: z.string().describe("F — observable people, characters, or objects in the shot."),
  character_block: z.string().describe("F — exact, stable analyst-observed character description repeated verbatim in every scene where that character appears; empty if no character is visible. Do not present it as the creator's original prompt."),
  room: z.string().describe("R — visible setting, environment, time of day when supported, and lighting; mark unknown details as unknown."),
  action: z.string().describe("A — one primary change from the beginning to the end of this scene, including its pacing."),
  movement: z.string().describe("M — camera framing and only camera movement supported by the visual evidence; say unknown if motion cannot be determined."),
  extras: z.string().describe("E — evidenced sound, speech, and stylistic choices. State when audio is unassessed; do not invent sounds."),
  dont_line: z.string().describe("E — an analyst continuity or avoidance rule for recreating this scene, clearly a recommendation rather than observed fact."),
});
export type FrameScene = z.infer<typeof FrameSceneSchema>;

export const VideoIntelligenceSchema = z.object({
  hook_analysis: z.object({
    verbal_hook: z.string().describe("First spoken sentence(s), verbatim. Empty string if no speech."),
    on_screen_text_hook: z.string().describe("Text overlay visible in the first ~3 seconds, verbatim. Empty if none."),
    visual_hook_description: z.string().describe("What the viewer sees in the first 3 seconds that stops the scroll."),
    hook_archetype: z.enum(HOOK_ARCHETYPES),
    retention_trigger: z.string().describe("The psychological lever, e.g. 'Fear of obsolescence'."),
  }),
  narrative_beats: z.array(
    z.object({
      timestamp_range: z.string().describe("Format 'M:SS - M:SS'"),
      beat_type: z.enum(BEAT_TYPES),
      summary: z.string(),
      on_screen_text: z.string().describe("Overlay text during this beat, empty if none."),
    }),
  ),
  frame_analysis: z.array(FrameSceneSchema).optional(),
  frame_analysis_meta: z.object({
    source: z.literal("watch"),
    detail: z.literal("balanced"),
    evidence_frames: z.number().int().nonnegative(),
    max_scene_seconds: z.literal(5),
    model: z.string(),
  }).optional(),
  structural_metrics: z.object({
    pacing_words_per_minute: z.number(),
    cta_type: z.enum(CTA_TYPES),
    cta_text: z.string(),
    loop_mechanic: z.string().describe("How the ending feeds back into the start, or 'None'."),
    pattern_interrupts: z.array(z.string()).describe("Visual/audio interrupts: zooms, cuts, SFX, b-roll swaps."),
  }),
  primary_topic_cluster: z.string().describe("Short, reusable topic label, e.g. 'SaaS Lead Gen'."),
  takeaways_for_remixing: z.array(z.string()),
});
export type VideoIntelligence = z.infer<typeof VideoIntelligenceSchema>;

export const RemixSchema = z.object({
  scripts: z.array(
    z.object({
      title: z.string(),
      angle: z.string().describe("How this variant adapts the outlier's mechanism to the brand."),
      hook_archetype: z.enum(HOOK_ARCHETYPES),
      beats: z.array(
        z.object({
          timestamp_range: z.string(),
          beat_type: z.enum(BEAT_TYPES),
          voiceover: z.string(),
          on_screen_text: z.string(),
          visual_direction: z.string(),
        }),
      ),
      caption: z.string(),
      cta: z.string(),
    }),
  ),
});
export type Remix = z.infer<typeof RemixSchema>;

export const DigestSchema = z.object({
  headline: z.string(),
  summary: z.string(),
  rising_formats: z.array(
    z.object({ name: z.string(), evidence: z.string(), example_video_ids: z.array(z.string()), recommendation: z.string() }),
  ),
  top_hooks: z.array(z.object({ video_id: z.string(), hook: z.string(), why_it_worked: z.string() })),
  fading_patterns: z.array(z.string()),
  experiments_to_run: z.array(z.string()),
});
export type Digest = z.infer<typeof DigestSchema>;
