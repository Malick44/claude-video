"use client";

import { useState } from "react";
import { multiplier, PLATFORM_LABEL } from "@/lib/format";
import type { Remix } from "@/lib/schema";

interface VideoOpt { id: string; handle: string; platform: string; hook_text: string | null; hook_archetype: string | null; outlier_multiplier: number | null }
interface Brand { id: string; name: string; context: string }

export function RemixStudio({ videos, brands: initialBrands, initialVideoId }: { videos: VideoOpt[]; brands: Brand[]; initialVideoId: string | null }) {
  const [videoId, setVideoId] = useState(initialVideoId ?? videos[0]?.id ?? "");
  const [brands, setBrands] = useState(initialBrands);
  const [brandId, setBrandId] = useState(initialBrands[0]?.id ?? "new");
  const [newBrand, setNewBrand] = useState({ name: "", context: "" });
  const [direction, setDirection] = useState("");
  const [result, setResult] = useState<Remix | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setLoading(true); setError(null); setResult(null);
    try {
      let id = brandId;
      if (brandId === "new") {
        const res = await fetch("/api/brands", { method: "POST", body: JSON.stringify(newBrand) });
        const brand = await res.json();
        if (!res.ok) throw new Error(brand.error);
        setBrands((b) => [...b, brand]); setBrandId(brand.id); id = brand.id;
      }
      const res = await fetch("/api/remix", { method: "POST", body: JSON.stringify({ videoId, brandProfileId: id, direction: direction || undefined }) });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error);
      setResult(json);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setLoading(false);
    }
  }

  const selected = videos.find((v) => v.id === videoId);

  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 text-sm">
        <label className="block space-y-1">
          <span className="text-xs uppercase tracking-wide text-zinc-500">Source outlier</span>
          <select value={videoId} onChange={(e) => setVideoId(e.target.value)} className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-2">
            {videos.map((v) => (
              <option key={v.id} value={v.id}>{multiplier(v.outlier_multiplier)} · @{v.handle} ({PLATFORM_LABEL[v.platform]}) — {v.hook_text?.slice(0, 60)}</option>
            ))}
          </select>
        </label>
        {selected && (
          <div className="rounded-md bg-zinc-950 p-3">
            <div className="text-xs text-fuchsia-300">{selected.hook_archetype}</div>
            <div className="mt-1">“{selected.hook_text}”</div>
          </div>
        )}
        <label className="block space-y-1">
          <span className="text-xs uppercase tracking-wide text-zinc-500">Brand</span>
          <select value={brandId} onChange={(e) => setBrandId(e.target.value)} className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-2">
            {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            <option value="new">+ New brand profile</option>
          </select>
        </label>
        {brandId === "new" ? (
          <>
            <input value={newBrand.name} onChange={(e) => setNewBrand({ ...newBrand, name: e.target.value })} placeholder="Brand name"
              className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2" />
            <textarea value={newBrand.context} onChange={(e) => setNewBrand({ ...newBrand, context: e.target.value })} rows={8}
              placeholder="Offer, audience, voice, proof points, lead magnets, claims to avoid…"
              className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2" />
          </>
        ) : (
          <p className="line-clamp-4 text-xs text-zinc-400">{brands.find((b) => b.id === brandId)?.context}</p>
        )}
        <textarea value={direction} onChange={(e) => setDirection(e.target.value)} rows={2} placeholder="Optional direction (e.g. 'promote the Q4 webinar')"
          className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2" />
        <button onClick={generate} disabled={loading || !videoId || (brandId === "new" && (!newBrand.name || !newBrand.context))}
          className="w-full rounded-md bg-fuchsia-600 py-2.5 font-medium text-white hover:bg-fuchsia-500 disabled:opacity-50">
          {loading ? "Writing 3 scripts…" : "Remix for my brand"}
        </button>
        {error && <p className="text-red-400">{error}</p>}
      </div>

      <div className="space-y-6">
        {!result && !loading && <p className="text-zinc-500">Pick an analyzed outlier and a brand profile to generate adapted scripts.</p>}
        {loading && <p className="animate-pulse text-zinc-400">Mapping beats and pacing onto your brand…</p>}
        {result?.scripts.map((s, i) => (
          <article key={i} className="rounded-lg border border-zinc-800">
            <header className="border-b border-zinc-800 p-4">
              <div className="text-xs text-fuchsia-300">Variant {i + 1} · {s.hook_archetype}</div>
              <h2 className="text-lg font-semibold">{s.title}</h2>
              <p className="text-sm text-zinc-400">{s.angle}</p>
            </header>
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-zinc-500">
                <tr><th className="px-4 py-2">Time</th><th className="px-4 py-2">Voiceover</th><th className="px-4 py-2">On-screen text</th><th className="px-4 py-2">Visual</th></tr>
              </thead>
              <tbody>
                {s.beats.map((b, j) => (
                  <tr key={j} className="border-t border-zinc-800 align-top">
                    <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-zinc-400">{b.timestamp_range}<div className="font-sans text-zinc-300">{b.beat_type}</div></td>
                    <td className="px-4 py-2">{b.voiceover}</td>
                    <td className="px-4 py-2 text-amber-300/90">{b.on_screen_text}</td>
                    <td className="px-4 py-2 text-zinc-400">{b.visual_direction}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <footer className="space-y-1 border-t border-zinc-800 p-4 text-sm">
              <div><span className="text-zinc-500">CTA:</span> {s.cta}</div>
              <div><span className="text-zinc-500">Caption:</span> {s.caption}</div>
              <button onClick={() => navigator.clipboard.writeText(s.beats.map((b) => `[${b.timestamp_range}] ${b.voiceover}`).join("\n"))}
                className="mt-2 rounded bg-zinc-800 px-2 py-1 text-xs hover:bg-zinc-700">Copy voiceover</button>
            </footer>
          </article>
        ))}
      </div>
    </div>
  );
}
