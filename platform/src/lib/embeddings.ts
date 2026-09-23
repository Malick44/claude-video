// 1536-d embeddings for pgvector (hook similarity + semantic search).
import OpenAI from "openai";
import { env } from "./env";

let client: OpenAI | null = null;

export async function embed(texts: string[]): Promise<number[][]> {
  client ??= new OpenAI({ apiKey: env.openaiKey() });
  const res = await client.embeddings.create({ model: env.embeddingModel(), input: texts, dimensions: 1536 });
  return res.data.sort((a, b) => a.index - b.index).map((d) => d.embedding);
}

/** pgvector literal */
export const toVector = (v: number[]) => `[${v.join(",")}]`;
