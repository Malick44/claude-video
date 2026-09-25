// Five-second FRAME scenes from watch's timestamped visual evidence.
import { readFile } from "node:fs/promises";
import type Anthropic from "@anthropic-ai/sdk";
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { z } from "zod";
import { frameWindows, FRAME_SCENE_MAX_SECONDS, type FrameWindow } from "../frame-windows";
import type { Transcript } from "../media/transcribe";
import type { WatchFrame } from "../media/watch";
import { fmtTs, timestampedLines } from "../pacing";
import { FrameSceneSchema, type FrameScene } from "../schema";
import { anthropic, baseParams } from "./client";

const FrameBatchSchema = z.object({
  scenes: z.array(FrameSceneSchema.omit({ timestamp_range: true }).extend({
    window_number: z.number().int().positive().describe("The 1-based WINDOW number supplied with this scene's evidence."),
  })),
});
const WINDOWS_PER_BATCH = 12; // one minute at five seconds per scene

const SYSTEM = `You are a careful video scene analyst. Return FRAME notes for the exact, fixed time windows supplied.
Each window is one scene, even when one shot or action continues across a boundary. Return exactly one scene per window, in order. Never merge windows or invent an extra scene.
F — Figure: name only people, characters, or objects supported by the frames. Give recurring characters one stable analyst-observed character block and repeat its wording VERBATIM whenever that character reappears. The creator's original prompt is unavailable unless provided; never claim to know it. Use an empty character block if no character is visible.
R — Room: visible setting, environmental detail, time of day only when evidenced, and lighting.
A — Action: one primary visible change from start to end, with pace. If the frames do not show a change, say what is held or what the transcript adds without inventing movement.
M — Movement: distinguish static framing and cuts from camera movement. Do not infer a pan, zoom, or tracking shot from stills alone.
E — Extras: supported speech, on-screen text, and style. Transcript proves words, not music or sound effects; state audio is unassessed when appropriate. The don't-line is an analyst recommendation about what a recreation should preserve or avoid, never a claim about the creator's instructions.
Use only the timecoded frames and transcript supplied. Be concise, specific, and explicit about uncertainty.`;

/** Keep opening/ending evidence plus a scene-change frame inside each window. */
function selectWindowFrames(frames: WatchFrame[], window: FrameWindow): WatchFrame[] {
  const inside = frames.filter((frame) => frame.t >= window.start && frame.t < window.end);
  if (inside.length <= 3) return inside;
  const middle = inside.slice(1, -1);
  const change = middle.find((frame) => frame.reason === "scene-change") ?? middle[Math.floor(middle.length / 2)];
  return [inside[0], change, inside[inside.length - 1]];
}

export async function analyzeFrameScenes(input: {
  durationSeconds: number;
  frames: WatchFrame[];
  transcript: Transcript;
}): Promise<{ scenes: FrameScene[]; model: string }> {
  const windows = frameWindows(input.durationSeconds);
  const scenes: FrameScene[] = [];
  let model = "";

  for (let offset = 0; offset < windows.length; offset += WINDOWS_PER_BATCH) {
    const batch = windows.slice(offset, offset + WINDOWS_PER_BATCH);
    const content: Anthropic.Beta.BetaContentBlockParam[] = [{
      type: "text",
      text: [
        `Analyze ${batch.length} consecutive FRAME scenes. Every scene has a maximum duration of ${FRAME_SCENE_MAX_SECONDS} seconds.`,
        `Return exactly ${batch.length} scene objects in the same order as the windows below. Set window_number to the exact WINDOW number shown for each.`,
        scenes.length ? `Previously observed character blocks — copy the complete wording exactly if the same character reappears:\n${[...new Set(scenes.map((scene) => scene.character_block).filter(Boolean))].join("\n\n")}` : "",
      ].filter(Boolean).join("\n\n"),
    }];

    for (const [index, window] of batch.entries()) {
      const evidence = selectWindowFrames(input.frames, window);
      if (!evidence.length) throw new Error(`watch returned no visual evidence for ${fmtTs(window.start)}-${fmtTs(window.end)}`);
      const words = input.transcript.words.filter((word) => word.start < window.end && word.end > window.start);
      content.push({
        type: "text",
        text: [
          `WINDOW ${offset + index + 1}: ${fmtTs(window.start)} - ${fmtTs(window.end)}`,
          `Transcript: ${timestampedLines(words).join(" ") || "(none available; speech/audio unassessed)"}`,
          `Frames: ${evidence.length} timestamped stills follow.`,
        ].join("\n"),
      });
      for (const frame of evidence) {
        content.push({ type: "text", text: `Frame at ${frame.t.toFixed(2)}s (${frame.reason})` });
        content.push({
          type: "image",
          source: { type: "base64", media_type: "image/jpeg", data: (await readFile(frame.path)).toString("base64") },
        });
      }
    }

    const response = await anthropic().beta.messages.parse({
      ...baseParams(),
      max_tokens: 16000,
      system: SYSTEM,
      messages: [{ role: "user", content }],
      output_config: { format: betaZodOutputFormat(FrameBatchSchema) },
    });
    if (response.stop_reason === "refusal") throw new Error("FRAME analysis declined by model");
    const parsed = response.parsed_output;
    if (!parsed || parsed.scenes.length !== batch.length) {
      throw new Error(`FRAME analysis returned ${parsed?.scenes.length ?? 0} scenes for ${batch.length} fixed windows`);
    }
    if (parsed.scenes.some((scene, index) => scene.window_number !== offset + index + 1)) {
      throw new Error("FRAME analysis returned scenes out of window order");
    }
    model = response.model;
    scenes.push(...parsed.scenes.map(({ window_number: _windowNumber, ...scene }, index) => ({
      ...scene,
      timestamp_range: `${fmtTs(batch[index].start)} - ${fmtTs(batch[index].end)}`,
    })));
  }

  return { scenes, model };
}
