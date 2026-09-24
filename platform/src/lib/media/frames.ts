// Keyframe extraction with FFmpeg: fixed hook frames (0.5s, 1.5s, 3.0s) plus
// scene-cut frames, which also give us a visual pacing metric (cuts / minute).
import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { run } from "./exec";

export const HOOK_TIMESTAMPS = [0.5, 1.5, 3.0];
export const SCENE_THRESHOLD = 0.35;
export const MAX_SCENE_FRAMES = 12;

export interface Keyframe {
  t: number;
  kind: "hook" | "scene";
  path: string;
}

export async function probeDuration(file: string): Promise<number | null> {
  const { stdout } = await run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file]);
  const d = Number(stdout.trim());
  return Number.isFinite(d) ? d : null;
}

/** Parse `pts_time:12.345` values from ffmpeg's showinfo filter output. */
export function parseShowinfoTimes(stderr: string): number[] {
  return [...stderr.matchAll(/showinfo.*?pts_time:\s*([\d.]+)/g)].map((m) => Number(m[1]));
}

/** Keep at most `max` cuts, evenly spread, and drop cuts inside the hook window (already covered). */
export function pickSceneCuts(times: number[], max = MAX_SCENE_FRAMES, minGap = 0.75): number[] {
  const deduped: number[] = [];
  for (const t of [...times].sort((a, b) => a - b)) {
    if (t < 3.25) continue;
    if (deduped.length === 0 || t - deduped[deduped.length - 1] >= minGap) deduped.push(t);
  }
  if (deduped.length <= max) return deduped;
  const step = deduped.length / max;
  return Array.from({ length: max }, (_, i) => deduped[Math.floor(i * step)]);
}

export async function extractKeyframes(
  file: string,
  dir: string,
  duration: number | null,
): Promise<{ frames: Keyframe[]; sceneCutTimes: number[] }> {
  const frames: Keyframe[] = [];

  for (const t of HOOK_TIMESTAMPS) {
    if (duration !== null && t >= duration) continue;
    const path = join(dir, `hook_${t.toFixed(1)}.jpg`);
    await run("ffmpeg", ["-v", "error", "-ss", String(t), "-i", file, "-frames:v", "1", "-vf", "scale=720:-2", "-q:v", "3", "-y", path]);
    frames.push({ t, kind: "hook", path });
  }

  // Scene detection pass (timestamps only), then grab the chosen cuts.
  const { stderr } = await run("ffmpeg", [
    "-v", "info", "-i", file, "-vf", `select='gt(scene,${SCENE_THRESHOLD})',showinfo`, "-an", "-f", "null", "-",
  ]);
  const sceneCutTimes = parseShowinfoTimes(stderr);
  for (const t of pickSceneCuts(sceneCutTimes)) {
    const path = join(dir, `scene_${t.toFixed(2)}.jpg`);
    await run("ffmpeg", ["-v", "error", "-ss", String(t), "-i", file, "-frames:v", "1", "-vf", "scale=720:-2", "-q:v", "4", "-y", path]);
    frames.push({ t, kind: "scene", path });
  }

  const written = new Set(await readdir(dir));
  return { frames: frames.filter((f) => written.has(f.path.split("/").pop()!)), sceneCutTimes };
}

export async function extractAudio(file: string, dir: string): Promise<string | null> {
  const out = join(dir, "audio.m4a");
  try {
    await run("ffmpeg", ["-v", "error", "-i", file, "-vn", "-ac", "1", "-c:a", "aac", "-b:a", "64k", "-y", out]);
    return out;
  } catch {
    return null; // silent video
  }
}
