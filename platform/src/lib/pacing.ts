// Deterministic pacing metrics — computed, not asked of the LLM.
import type { Word } from "./media/transcribe";

export function wordsPerMinute(words: Pick<Word, "start" | "end">[]): number | null {
  if (words.length < 3) return null;
  const spoken = words[words.length - 1].end - words[0].start;
  if (spoken <= 0) return null;
  return Math.round((words.length / spoken) * 60);
}

export function cutsPerMinute(cutTimes: number[], duration: number | null): number | null {
  if (!duration || duration <= 0) return null;
  return Math.round((cutTimes.length / duration) * 60 * 10) / 10;
}

export function fmtTs(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** "0:04 - 0:18" -> [4, 18] */
export function parseRange(range: string): [number, number] | null {
  const m = range.match(/(\d+):(\d{1,2})\s*[-–]\s*(\d+):(\d{1,2})/);
  if (!m) return null;
  return [Number(m[1]) * 60 + Number(m[2]), Number(m[3]) * 60 + Number(m[4])];
}

/** Group words into ~`maxSec` timestamped lines, for prompting and display. */
export function timestampedLines(words: Word[], maxSec = 4): string[] {
  const lines: string[] = [];
  let cur: Word[] = [];
  for (const w of words) {
    if (cur.length && (w.end - cur[0].start > maxSec || /[.!?]$/.test(cur[cur.length - 1].word))) {
      lines.push(`[${fmtTs(cur[0].start)}] ${cur.map((x) => x.word).join(" ")}`);
      cur = [];
    }
    cur.push(w);
  }
  if (cur.length) lines.push(`[${fmtTs(cur[0].start)}] ${cur.map((x) => x.word).join(" ")}`);
  return lines;
}

/** Word budget per beat so a remix keeps the outlier's timing and pacing. */
export function beatWordBudgets(beats: { timestamp_range: string }[], wpm: number): number[] {
  return beats.map((b) => {
    const r = parseRange(b.timestamp_range);
    return r ? Math.max(1, Math.round(((r[1] - r[0]) / 60) * wpm)) : 0;
  });
}
