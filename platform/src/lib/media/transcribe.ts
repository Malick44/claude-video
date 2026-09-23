// Deepgram Nova-3: word-level timestamps + sentiment tags.
import { readFile } from "node:fs/promises";
import { env } from "../env";

export interface Word {
  word: string;
  start: number;
  end: number;
  confidence: number;
  sentiment?: string;
}

export interface Transcript {
  text: string;
  words: Word[];
  sentimentSegments: { text: string; start: number; end: number; sentiment: string }[];
}

interface DeepgramResponse {
  results: {
    channels: { alternatives: { transcript: string; words: (Word & { punctuated_word?: string; sentiment?: string })[] }[] }[];
    sentiments?: { segments: { text: string; start_word: number; end_word: number; sentiment: string }[] };
  };
}

export async function transcribe(audioPath: string): Promise<Transcript> {
  const url = new URL("https://api.deepgram.com/v1/listen");
  for (const [k, v] of Object.entries({ model: "nova-3", smart_format: "true", punctuate: "true", sentiment: "true", detect_language: "true" })) {
    url.searchParams.set(k, v);
  }
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Token ${env.deepgramKey()}`, "Content-Type": "audio/mp4" },
    body: new Uint8Array(await readFile(audioPath)),
  });
  if (!res.ok) throw new Error(`Deepgram failed (${res.status}): ${await res.text()}`);
  return parseDeepgram((await res.json()) as DeepgramResponse);
}

export function parseDeepgram(json: DeepgramResponse): Transcript {
  const alt = json.results.channels[0]?.alternatives[0];
  const words: Word[] = (alt?.words ?? []).map((w) => ({
    word: w.punctuated_word ?? w.word,
    start: w.start,
    end: w.end,
    confidence: w.confidence,
    ...(w.sentiment ? { sentiment: w.sentiment } : {}),
  }));
  const sentimentSegments = (json.results.sentiments?.segments ?? []).map((s) => ({
    text: s.text,
    start: words[s.start_word]?.start ?? 0,
    end: words[Math.min(s.end_word, words.length - 1)]?.end ?? 0,
    sentiment: s.sentiment,
  }));
  return { text: alt?.transcript ?? "", words, sentimentSegments };
}
