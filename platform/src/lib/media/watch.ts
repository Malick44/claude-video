// Run the watch skill's scene-aware extractor on an already-downloaded video.
// FRAME analysis needs evidence across the whole timeline, so every <=5s
// window gets two pinned frames even if the scene detector finds no cuts.
import { access, mkdtemp, realpath, stat } from "node:fs/promises";
import { join, resolve, sep } from "node:path";
import { frameWindows } from "../frame-windows";
import { run } from "./exec";

export interface WatchFrame {
  t: number;
  path: string;
  reason: string;
}

interface WatchReport {
  duration_seconds: number;
  frames: { timestamp_seconds: number; path: string; reason: string }[];
}

function parseWatchReport(stdout: string): WatchReport {
  let value: unknown;
  try {
    value = JSON.parse(stdout);
  } catch {
    throw new Error("watch.py did not return JSON; check that this watch skill version supports --json");
  }
  if (!value || typeof value !== "object") throw new Error("watch.py returned an invalid report");
  const report = value as Record<string, unknown>;
  if (typeof report.duration_seconds !== "number" || !Number.isFinite(report.duration_seconds) || report.duration_seconds <= 0) {
    throw new Error("watch.py report has no valid video duration");
  }
  if (!Array.isArray(report.frames) || report.frames.length === 0) {
    throw new Error("watch.py extracted no frames");
  }
  for (const frame of report.frames) {
    if (!frame || typeof frame !== "object") throw new Error("watch.py returned an invalid frame entry");
    const f = frame as Record<string, unknown>;
    if (typeof f.timestamp_seconds !== "number" || !Number.isFinite(f.timestamp_seconds) || f.timestamp_seconds < 0 ||
        typeof f.path !== "string" || !f.path || typeof f.reason !== "string" || !f.reason) {
      throw new Error("watch.py returned a frame without a timestamp, path, or reason");
    }
  }
  return report as unknown as WatchReport;
}

/** Extract timecoded frames using watch.py; the caller owns `dir` and its cleanup. */
export async function extractWatchFrames(
  file: string,
  dir: string,
  durationSeconds: number,
): Promise<{ frames: WatchFrame[]; durationSeconds: number }> {
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
    throw new Error("Watch frame extraction requires a positive video duration");
  }
  const windows = frameWindows(durationSeconds);
  if (!windows.length) throw new Error("Watch frame extraction could not create FRAME windows");

  const pins = windows.flatMap(({ start, end }) => {
    const actualEnd = Math.min(end, durationSeconds);
    const width = actualEnd - start;
    if (width <= 0) return [];
    const offset = Math.min(0.25, width / 4);
    return [start + offset, actualEnd - offset];
  });
  // Pinned frames are reserved first by watch.py. Leave extra capacity for
  // scene changes, which can reveal action between the deterministic samples.
  const maxFrames = pins.length + Math.max(24, Math.ceil(windows.length * 1.5));
  const skillDir = resolve(process.env.WATCH_SKILL_DIR || join(process.cwd(), "..", "skills", "watch"));
  const script = join(skillDir, "scripts", "watch.py");
  try {
    await access(script);
  } catch {
    throw new Error(`Watch skill script missing at ${script}; install the skill or set WATCH_SKILL_DIR`);
  }

  const work = await mkdtemp(join(resolve(dir), "watch-"));
  let stdout: string;
  try {
    ({ stdout } = await run("python3", [
      script,
      resolve(file),
      "--json",
      "--detail", "balanced",
      "--no-whisper",
      "--out-dir", work,
      "--timestamps", pins.map((t) => t.toFixed(2)).join(","),
      "--max-frames", String(maxFrames),
    ], Math.max(300_000, Math.min(3_600_000, windows.length * 12_000))));
  } catch (error) {
    throw new Error(`Watch skill extraction failed: ${error instanceof Error ? error.message : String(error)}. Check python3, ffmpeg, and the local video file.`);
  }

  const report = parseWatchReport(stdout);
  const frames: WatchFrame[] = [];
  const outputRoot = await realpath(work);
  for (const frame of report.frames) {
    const path = await realpath(frame.path).catch(() => null);
    if (!path) throw new Error(`watch.py reported a missing frame: ${frame.path}`);
    if (!path.startsWith(`${outputRoot}${sep}`)) throw new Error(`watch.py returned a frame outside its output directory: ${path}`);
    const fileStat = await stat(path).catch(() => null);
    if (!fileStat?.isFile()) throw new Error(`watch.py reported a missing frame: ${path}`);
    frames.push({ t: frame.timestamp_seconds, path, reason: frame.reason });
  }
  frames.sort((a, b) => a.t - b.t);

  const missingWindow = windows.findIndex(({ start, end }, i) =>
    !frames.some(({ t }) => t >= start - 0.01 && t < Math.min(end, durationSeconds) + (i === windows.length - 1 ? 0.01 : 0)));
  if (missingWindow !== -1) {
    const { start, end } = windows[missingWindow];
    throw new Error(`Watch skill missed FRAME window ${missingWindow + 1} (${start.toFixed(2)}–${end.toFixed(2)}s); retry extraction or inspect the source video`);
  }

  return { frames, durationSeconds: report.duration_seconds };
}
