import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { frameWindows } from "../frame-windows";
import { extractWatchFrames } from "./watch";

function hasCommand(command: string): boolean {
  try { execFileSync(command, [command === "python3" ? "--version" : "-version"], { stdio: "ignore" }); return true; } catch { return false; }
}

const script = join(resolve(process.cwd(), "..", "skills", "watch"), "scripts", "watch.py");
const canRun = hasCommand("ffmpeg") && hasCommand("ffprobe") && hasCommand("python3") && existsSync(script);

describe.skipIf(!canRun)("extractWatchFrames (watch skill)", () => {
  let dir: string;
  afterAll(async () => { if (dir) await rm(dir, { recursive: true, force: true }); });

  it("keeps visual evidence inside every FRAME window", async () => {
    dir = await mkdtemp(join(tmpdir(), "watch-adapter-test-"));
    const clip = join(dir, "clip.mp4");
    execFileSync("ffmpeg", [
      "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=160x288:r=10:d=12",
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", clip,
    ]);

    const result = await extractWatchFrames(clip, dir, 12);
    expect(result.durationSeconds).toBeGreaterThanOrEqual(11.9);
    expect(result.frames.length).toBeGreaterThanOrEqual(6);
    for (const { start, end } of frameWindows(12)) {
      expect(result.frames.some(({ t }) => t >= start && t < end)).toBe(true);
    }
    expect(result.frames.every(({ path }) => existsSync(path))).toBe(true);
  }, 60_000);
});
