import { describe, expect, it } from "vitest";
import { assertFrameSceneWindows, frameWindows } from "./frame-windows";
import { fmtTs } from "./pacing";

describe("FRAME scene windows", () => {
  it("covers a 90-second video in exactly five-second scenes", () => {
    const windows = frameWindows(90);
    expect(windows).toHaveLength(18);
    expect(windows[0]).toEqual({ start: 0, end: 5 });
    expect(windows.at(-1)).toEqual({ start: 85, end: 90 });
    expect(frameWindows(87.765).at(-1)).toEqual({ start: 85, end: 88 });
    expect(windows.every(({ start, end }) => end - start <= 5)).toBe(true);
    expect(() => assertFrameSceneWindows(
      windows.map(({ start, end }) => ({ timestamp_range: `${fmtTs(start)} - ${fmtTs(end)}` })),
      90,
    )).not.toThrow();
  });

  it("rejects a long or missing scene even if a model returns it", () => {
    const windows = frameWindows(12);
    const scenes = windows.map(({ start, end }) => ({ timestamp_range: `${fmtTs(start)} - ${fmtTs(end)}` }));
    scenes[1].timestamp_range = "0:05 - 0:11";
    expect(() => assertFrameSceneWindows(scenes, 12)).toThrow(/at most five seconds/);
    expect(() => assertFrameSceneWindows(scenes.slice(0, 2), 12)).toThrow(/does not cover/);
  });
});
