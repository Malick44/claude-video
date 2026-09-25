"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

function useAction(url: string, body?: unknown) {
  const [state, setState] = useState<"idle" | "busy" | "queued" | "error">("idle");
  return {
    state,
    run: async () => {
      setState("busy");
      const res = await fetch(url, { method: "POST", body: JSON.stringify(body ?? {}) });
      setState(res.ok ? "queued" : "error");
    },
  };
}

export function DigestTrigger() {
  const a = useAction("/api/digest");
  return (
    <button onClick={a.run} disabled={a.state === "busy"} className="rounded-md bg-zinc-800 px-3 py-1.5 text-sm hover:bg-zinc-700">
      {a.state === "queued" ? "Queued ✓" : a.state === "error" ? "Failed" : "Generate now"}
    </button>
  );
}

export function IngestTrigger() {
  const a = useAction("/api/ingest");
  return (
    <button onClick={a.run} disabled={a.state === "busy"} className="rounded-md bg-zinc-800 px-3 py-1.5 text-sm hover:bg-zinc-700">
      {a.state === "queued" ? "Scrape queued ✓" : a.state === "error" ? "Failed" : "Run ingest now"}
    </button>
  );
}

export function AddCompetitor() {
  const router = useRouter();
  const [form, setForm] = useState({ platform: "tiktok", handle: "", niche: "" });
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const res = await fetch("/api/competitors", { method: "POST", body: JSON.stringify(form) });
        if (!res.ok) return setError((await res.json()).error);
        setForm({ ...form, handle: "" }); setError(null); router.refresh();
      }}
      className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm"
    >
      <select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })} className="rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5">
        <option value="tiktok">TikTok</option><option value="instagram">Instagram Reels</option><option value="youtube">YouTube Shorts</option><option value="youtube_long">YouTube Long</option>
      </select>
      <input value={form.handle} onChange={(e) => setForm({ ...form, handle: e.target.value })} placeholder="@handle" required
        className="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-1.5" />
      <input value={form.niche} onChange={(e) => setForm({ ...form, niche: e.target.value })} placeholder="Niche (optional)"
        className="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-1.5" />
      <button className="rounded-md bg-white px-3 py-1.5 font-medium text-black">Track</button>
      {error && <span className="text-red-400">{error}</span>}
    </form>
  );
}

export function ToggleActive({ id, active }: { id: string; active: boolean }) {
  const router = useRouter();
  return (
    <button
      onClick={async () => { await fetch("/api/competitors", { method: "PATCH", body: JSON.stringify({ id, active: !active }) }); router.refresh(); }}
      className={`rounded-full px-2 py-0.5 text-xs ${active ? "bg-emerald-500/20 text-emerald-300" : "bg-zinc-800 text-zinc-500"}`}
    >
      {active ? "Tracking" : "Paused"}
    </button>
  );
}
