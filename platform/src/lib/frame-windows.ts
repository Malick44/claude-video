/** Fixed time windows make the FRAME scene limit a data invariant, not a prompt suggestion. */
export const FRAME_SCENE_MAX_SECONDS = 5;

export interface FrameWindow {
  start: number;
  end: number;
}

export function frameWindows(durationSeconds: number): FrameWindow[] {
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
    throw new Error("FRAME analysis needs a positive video duration");
  }

  // The UI displays whole seconds. Round the media duration to that same
  // precision so sub-frame tails do not create an unevidenced extra scene.
  const end = Math.max(1, Math.round(durationSeconds));
  const windows: FrameWindow[] = [];
  for (let start = 0; start < end; start += FRAME_SCENE_MAX_SECONDS) {
    windows.push({ start, end: Math.min(start + FRAME_SCENE_MAX_SECONDS, end) });
  }
  return windows;
}

export function assertFrameSceneWindows(
  scenes: { timestamp_range: string }[],
  durationSeconds: number,
): void {
  const expected = frameWindows(durationSeconds);
  if (scenes.length !== expected.length) {
    throw new Error(`FRAME scene count ${scenes.length} does not cover ${expected.length} five-second windows`);
  }
  for (const [index, scene] of scenes.entries()) {
    const { start, end } = expected[index];
    const label = `${Math.floor(start / 60)}:${String(start % 60).padStart(2, "0")} - ${Math.floor(end / 60)}:${String(end % 60).padStart(2, "0")}`;
    if (scene.timestamp_range !== label || end - start > FRAME_SCENE_MAX_SECONDS) {
      throw new Error(`FRAME scene ${index + 1} must cover ${label} (at most five seconds)`);
    }
  }
}
