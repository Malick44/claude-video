import { describe, expect, it } from "vitest";
import { parseShowinfoTimes, pickSceneCuts } from "./frames";
import { parseDeepgram } from "./transcribe";
import { beatWordBudgets, cutsPerMinute, parseRange, timestampedLines, wordsPerMinute } from "../pacing";

describe("frames", () => {
  it("parses showinfo pts_time", () => {
    const log = "[Parsed_showinfo_1 @ 0x1] n:0 pts:1234 pts_time:4.12 duration\n[Parsed_showinfo_1 @ 0x1] n:1 pts:99 pts_time:9.5 x";
    expect(parseShowinfoTimes(log)).toEqual([4.12, 9.5]);
  });
  it("drops hook-window cuts, dedupes close cuts, caps count", () => {
    expect(pickSceneCuts([1, 3.5, 3.9, 5, 8])).toEqual([3.5, 5, 8]);
    expect(pickSceneCuts(Array.from({ length: 40 }, (_, i) => 4 + i), 5)).toHaveLength(5);
  });
});

describe("transcript + pacing", () => {
  const dg = {
    results: {
      channels: [{ alternatives: [{ transcript: "Stop writing blogs. Seriously.", words: [
        { word: "stop", punctuated_word: "Stop", start: 0.1, end: 0.4, confidence: 0.99, sentiment: "negative" },
        { word: "writing", start: 0.4, end: 0.8, confidence: 0.98 },
        { word: "blogs", punctuated_word: "blogs.", start: 0.8, end: 1.2, confidence: 0.97 },
        { word: "seriously", punctuated_word: "Seriously.", start: 1.5, end: 2.1, confidence: 0.95 },
      ] }] }],
      sentiments: { segments: [{ text: "Stop writing blogs.", start_word: 0, end_word: 2, sentiment: "negative" }] },
    },
  };
  it("parses Deepgram output", () => {
    const t = parseDeepgram(dg);
    expect(t.words[0]).toMatchObject({ word: "Stop", sentiment: "negative" });
    expect(t.sentimentSegments[0]).toMatchObject({ start: 0.1, end: 1.2, sentiment: "negative" });
    expect(timestampedLines(t.words)).toEqual(["[0:00] Stop writing blogs.", "[0:02] Seriously."]);
    expect(wordsPerMinute(t.words)).toBe(120);
  });
  it("computes cut rate and beat budgets", () => {
    expect(cutsPerMinute([4, 8, 12], 30)).toBe(6);
    expect(parseRange("0:04 - 0:18")).toEqual([4, 18]);
    expect(beatWordBudgets([{ timestamp_range: "0:00 - 0:04" }, { timestamp_range: "0:04 - 0:18" }], 180)).toEqual([12, 42]);
  });
});
