"use client";

import { useState } from "react";
import { VideoDrawer } from "@/components/VideoDrawer";
import { compact, multiplier, omTone, PLATFORM_LABEL } from "@/lib/format";
import type { FeedRow } from "@/lib/types";

const EXAMPLES = ["cold email pricing with high saves", "founder story about getting fired", "tool comparison with split screen"];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FeedRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBySaves, setSortBySaves] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  async function search(q: string) {
    setQuery(q); setLoading(true); setError(null);
    // "…with high saves" is a metric filter, not a topic: sort by saves when asked.
    setSortBySaves(/\bsaves?\b/i.test(q));
    try {
      const res = await fetch("/api/search", { method: "POST", body: JSON.stringify({ query: q }) });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error);
      setResults(json.results);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setLoading(false);
    }
  }

  const shown = results && sortBySaves ? [...results].sort((a, b) => b.saves / Math.max(b.views, 1) - a.saves / Math.max(a.views, 1)) : results;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Semantic Search</h1>
        <p className="text-sm text-zinc-400">Search hooks, beats and transcripts by meaning across every tracked competitor.</p>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); if (query.trim()) void search(query); }} className="flex gap-2">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find videos talking about…"
          className="flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2.5 outline-none focus:border-zinc-500" />
        <button disabled={loading} className="rounded-md bg-white px-5 font-medium text-black disabled:opacity-50">{loading ? "Searching…" : "Search"}</button>
      </form>
      <div className="flex flex-wrap gap-2 text-xs">
        {EXAMPLES.map((ex) => (
          <button key={ex} onClick={() => search(ex)} className="rounded-full border border-zinc-700 px-3 py-1 text-zinc-400 hover:text-white">{ex}</button>
        ))}
      </div>
      {error && <p className="text-red-400">{error}</p>}
      {shown && (
        <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
          {shown.length === 0 && <li className="p-6 text-center text-zinc-500">No matches.</li>}
          {shown.map((r) => (
            <li key={r.id}>
              <button onClick={() => setOpenId(r.id)} className="flex w-full items-center gap-4 p-3 text-left hover:bg-zinc-900">
                {r.thumbnail_url ? <img src={r.thumbnail_url} alt="" className="h-20 w-12 rounded object-cover" /> : <div className="h-20 w-12 rounded bg-zinc-800" />}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 text-xs text-zinc-400">
                    <span className="font-medium text-zinc-200">@{r.handle}</span>{PLATFORM_LABEL[r.platform]} · {r.hook_archetype}
                  </div>
                  <div className="mt-1 line-clamp-2 text-sm">{r.hook_text ?? r.caption}</div>
                  <div className="mt-1 text-xs tabular-nums text-zinc-500">{compact(r.views)} views · {compact(r.saves)} saves · {r.primary_topic_cluster}</div>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${omTone(r.outlier_multiplier)}`}>{multiplier(r.outlier_multiplier)}</span>
                <span className="w-12 text-right text-xs tabular-nums text-zinc-500">{((r.similarity ?? 0) * 100).toFixed(0)}%</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <VideoDrawer videoId={openId} onClose={() => setOpenId(null)} />
    </div>
  );
}
