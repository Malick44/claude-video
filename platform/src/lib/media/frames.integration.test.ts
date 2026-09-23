// Runs only when ffmpeg is installed: synthesizes a clip with hard cuts and
// checks hook frames + scene-cut detection.
import { execFileSync } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { extractAudio, extractKeyframes, probeDuration } from "./frames";

const hasFfmpeg = (() => {
  try { execFileSync("ffmpeg", ["-version"], { stdio: "ignore" }); return true; } catch { return false; }
})();

describe.skipIf(!hasFfmpeg)("extractKeyframes (ffmpeg)", () => {
  let dir: string;
  afterAll(async () => dir && rm(dir, { recursive: true, force: true }));

  it("extracts hook frames and detects hard cuts", async () => {
    dir = await mkdtemp(join(tmpdir(), "frames-test-"));
    const clip = join(dir, "clip.mp4");
    // 4 solid-colour segments of 3s each -> cuts at 3, 6, 9s; plus a sine audio track.
    const colors = ["red", "blue", "green", "white"];
    execFileSync("ffmpeg", [
      "-v", "error",
      ...colors.flatMap((c) => ["-f", "lavfi", "-i", `color=c=${c}:s=360x640:d=3:r=25`]),
      "-f", "lavfi", "-i", "sine=frequency=440:duration=12",
      "-filter_complex", `${colors.map((_, i) => `[${i}:v]`).join("")}concat=n=${colors.length}:v=1:a=0[v]`,
      "-map", "[v]", "-map", `${colors.length}:a`, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-y", clip,
    ]);

    const duration = await probeDuration(clip);
    expect(duration).toBeGreaterThan(11);
    const { frames, sceneCutTimes } = await extractKeyframes(clip, dir, duration);
    expect(frames.filter((f) => f.kind === "hook").map((f) => f.t)).toEqual([0.5, 1.5, 3.0]);
    expect(sceneCutTimes.map(Math.round)).toEqual([3, 6, 9]);
    // The cut at 3s is inside the hook window and already covered.
    expect(frames.filter((f) => f.kind === "scene").map((f) => Math.round(f.t))).toEqual([6, 9]);
    expect(await extractAudio(clip, dir)).toMatch(/audio\.m4a$/);
  }, 60_000);
});
