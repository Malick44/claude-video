"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { compact, multiplier, omTone, pct, PLATFORM_LABEL, shortDate } from "@/lib/format";
import { fmtTs, parseRange } from "@/lib/pacing";
import type { VideoIntelligence } from "@/lib/schema";

interface Detail {
  video: {
    id: string; platform: string; video_url: string; media_url: string | null; thumbnail_url: string | null; caption: string | null;
    published_at: string | null; duration_seconds: number | null; views: number; likes: number; comments: number; shares: number; saves: number;
    outlier_multiplier: number | null; engagement_rate: number | null; processing_status: string; processing_error: string | null;
    raw_transcript: string | null; transcript_words: { word: string; start: number; end: number }[] | null;
    keyframes: { frames: { t: number; kind: string; url: string }[]; cuts_per_minute: number | null; scene_cut_times: number[] } | null;
    competitors: { handle: string; follower_count: number | null; median_views_last_20: number | null };
  };
  intelligence: { analysis_json: VideoIntelligence; model: string } | null;
  snapshots: { captured_at: string; age_bucket: string | null; views: number }[];
  similar: { video_id: string; hook_text: string; hook_archetype: string; similarity: number }[];
}

const BEAT_TONE: Record<string, string> = {
  Hook: "border-fuchsia-500",
  "Agitation & Proof": "border-amber-500",
  "Actionable Pivot": "border-emerald-500",
  Demonstration: "border-emerald-500",
  "Payoff / Reveal": "border-sky-500",
  "Call To Action": "border-rose-500",
};

export function VideoDrawer({ videoId, onClose }: { videoId: string | null; onClose: () => void }) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [time, setTime] = useState(0);
  const [videoFailed, setVideoFailed] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (!videoId) return;
    setDetail(null); setError(null); setTime(0); setVideoFailed(false);
    fetch(`/api/videos/${videoId}`)
      .then((r) => (r.ok ? r.json() : r.json().then((j) => Promise.reject(new Error(j.error)))))
      .then(setDetail)
      .catch((e) => setError(String(e.message ?? e)));
  }, [videoId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!videoId) return null;
  const seek = (t: number) => {
    if (videoRef.current) { videoRef.current.currentTime = t; void videoRef.current.play(); }
  };

  const a = detail?.intelligence?.analysis_json;
  const v = detail?.video;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/60" onClick={onClose}>
      <aside onClick={(e) => e.stopPropagation()} className="h-full w-full max-w-5xl overflow-y-auto border-l border-zinc-800 bg-zinc-950 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-zinc-800 bg-zinc-950/95 px-5 py-3">
          <div className="text-sm">
            {v ? (<><span className="font-semibold">@{v.competitors.handle}</span> <span className="text-zinc-500">· {PLATFORM_LABEL[v.platform]} · {shortDate(v.published_at)}</span></>) : "Loading…"}
          </div>
          <div className="flex items-center gap-2">
            {v && <a href={v.video_url} target="_blank" rel="noreferrer" className="rounded-md px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800">Open original ↗</a>}
            {a && <Link href={`/remix?video=${videoId}`} className="rounded-md bg-fuchsia-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-fuchsia-500">Remix for my brand</Link>}
            <button onClick={onClose} className="rounded-md px-2 py-1 text-zinc-400 hover:bg-zinc-800" aria-label="Close">✕</button>
          </div>
        </div>

        {error && <p className="p-5 text-red-400">{error}</p>}
        {v && (
          <div className="grid gap-6 p-5 md:grid-cols-[300px_1fr]">
            {/* Left: player + stats */}
            <div className="space-y-4">
              <div className="aspect-[9/16] overflow-hidden rounded-lg bg-black md:sticky md:top-20">
                {v.media_url && !videoFailed ? (
                  <video ref={videoRef} src={v.media_url} poster={v.thumbnail_url ?? undefined} controls playsInline className="h-full w-full"
                    onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)} onError={() => setVideoFailed(true)} />
                ) : (
                  <a href={v.video_url} target="_blank" rel="noreferrer" className="relative block h-full">
                    {v.thumbnail_url && <img src={v.thumbnail_url} alt="" className="h-full w-full object-cover opacity-70" />}
                    <span className="absolute inset-0 flex items-center justify-center text-sm text-white">{v.media_url ? "CDN link expired — " : ""}Watch on {PLATFORM_LABEL[v.platform]} ↗</span>
                  </a>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <Stat label="Outlier" value={<span className={`rounded-full px-2 py-0.5 ${omTone(v.outlier_multiplier)}`}>{multiplier(v.outlier_multiplier)}</span>} />
                <Stat label="Engagement rate" value={pct(v.engagement_rate)} />
                <Stat label="Views" value={compact(v.views)} />
                <Stat label="Creator baseline" value={compact(v.competitors.median_views_last_20)} />
                <Stat label="Saves" value={compact(v.saves)} />
                <Stat label="Shares" value={compact(v.shares)} />
                <Stat label="Pacing" value={a ? `${a.structural_metrics.pacing_words_per_minute} wpm` : "—"} />
                <Stat label="Cuts / min" value={v.keyframes?.cuts_per_minute ?? "—"} />
              </div>
              {detail.snapshots.length > 1 && <Trajectory snapshots={detail.snapshots} />}
            </div>

            {/* Right: breakdown */}
            <div className="space-y-6">
              {!a ? (
                <div className="rounded-lg border border-zinc-800 p-4 text-sm text-zinc-400">
                  Not analyzed yet ({v.processing_status}). {v.processing_error && <span className="text-red-400">{v.processing_error}</span>}
                  <button onClick={() => fetch("/api/ingest", { method: "POST", body: JSON.stringify({ videoId }) })} className="ml-2 rounded bg-zinc-800 px-2 py-1 text-zinc-200 hover:bg-zinc-700">
                    Analyze now
                  </button>
                </div>
              ) : (
                <>
                  <section className="rounded-lg border border-fuchsia-900/60 bg-fuchsia-950/20 p-4">
                    <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                      <span className="rounded-full bg-fuchsia-500/20 px-2 py-0.5 font-medium text-fuchsia-300">{a.hook_analysis.hook_archetype}</span>
                      <span className="text-zinc-400">Trigger: {a.hook_analysis.retention_trigger}</span>
                    </div>
                    <p className="text-lg font-medium leading-snug">“{a.hook_analysis.verbal_hook || "(no spoken hook)"}”</p>
                    {a.hook_analysis.on_screen_text_hook && <p className="mt-2 text-sm"><span className="text-zinc-500">On-screen:</span> {a.hook_analysis.on_screen_text_hook}</p>}
                    <p className="mt-2 text-sm text-zinc-300"><span className="text-zinc-500">Visual:</span> {a.hook_analysis.visual_hook_description}</p>
                  </section>

                  <section>
                    <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Beat timeline</h3>
                    <ol className="space-y-2">
                      {a.narrative_beats.map((b, i) => {
                        const r = parseRange(b.timestamp_range);
                        const active = r ? time >= r[0] && time < r[1] : false;
                        return (
                          <li key={i}>
                            <button onClick={() => r && seek(r[0])}
                              className={`w-full rounded-r-md border-l-4 px-3 py-2 text-left text-sm transition ${BEAT_TONE[b.beat_type] ?? "border-zinc-600"} ${active ? "bg-zinc-800" : "bg-zinc-900 hover:bg-zinc-800/70"}`}>
                              <div className="flex items-center gap-2 text-xs text-zinc-400">
                                <span className="font-mono">{b.timestamp_range}</span><span className="font-semibold text-zinc-200">{b.beat_type}</span>
                              </div>
                              <div className="mt-1">{b.summary}</div>
                              {b.on_screen_text && <div className="mt-1 text-xs text-amber-300/90">▣ {b.on_screen_text}</div>}
                            </button>
                          </li>
                        );
                      })}
                    </ol>
                  </section>

                  <section className="grid gap-3 text-sm sm:grid-cols-2">
                    <Card title="CTA">{a.structural_metrics.cta_type}{a.structural_metrics.cta_text && <> — <i>{a.structural_metrics.cta_text}</i></>}</Card>
                    <Card title="Loop mechanic">{a.structural_metrics.loop_mechanic}</Card>
                    <Card title="Topic cluster">{a.primary_topic_cluster}</Card>
                    <Card title="Pattern interrupts">{a.structural_metrics.pattern_interrupts.join(" · ") || "—"}</Card>
                  </section>

                  <section>
                    <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Takeaways for remixing</h3>
                    <ul className="list-disc space-y-1 pl-5 text-sm">{a.takeaways_for_remixing.map((t, i) => <li key={i}>{t}</li>)}</ul>
                  </section>
                </>
              )}

              {v.keyframes?.frames?.length ? (
                <section>
                  <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Keyframes</h3>
                  <div className="flex gap-2 overflow-x-auto pb-2">
                    {v.keyframes.frames.map((f) => (
                      <button key={f.url} onClick={() => seek(f.t)} className="shrink-0 text-center text-[10px] text-zinc-500">
                        <img src={f.url} alt={`Frame at ${f.t}s`} className={`h-32 rounded ${f.kind === "hook" ? "ring-2 ring-fuchsia-500" : ""}`} />
                        {fmtTs(f.t)} {f.kind === "hook" ? "hook" : "cut"}
                      </button>
                    ))}
                  </div>
                </section>
              ) : null}

              {v.transcript_words?.length ? (
                <section>
                  <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Transcript</h3>
                  <p className="text-sm leading-relaxed text-zinc-400">
                    {v.transcript_words.map((w, i) => (
                      <span key={i} onClick={() => seek(w.start)} className={`cursor-pointer ${time >= w.start && time < w.end ? "bg-fuchsia-500/40 text-white" : "hover:text-zinc-200"}`}>{w.word} </span>
                    ))}
                  </p>
                </section>
              ) : null}

              {detail.similar.length > 0 && (
                <section>
                  <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Similar hooks across the niche</h3>
                  <ul className="space-y-1 text-sm">
                    {detail.similar.map((s) => (
                      <li key={s.video_id} className="flex gap-2">
                        <span className="w-12 shrink-0 tabular-nums text-zinc-500">{(s.similarity * 100).toFixed(0)}%</span>
                        <span>{s.hook_text} <span className="text-zinc-500">({s.hook_archetype})</span></span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md bg-zinc-900 px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="mt-0.5 font-semibold tabular-nums">{value}</div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-900 p-3">
      <div className="mb-1 text-[11px] uppercase tracking-wide text-zinc-500">{title}</div>
      {children}
    </div>
  );
}

/** Views over time (ingest / d1 / d3 / d7 snapshots): the viral half-life. */
function Trajectory({ snapshots }: { snapshots: Detail["snapshots"] }) {
  const w = 280, h = 64, pad = 4;
  const t0 = new Date(snapshots[0].captured_at).getTime();
  const t1 = new Date(snapshots[snapshots.length - 1].captured_at).getTime() || t0 + 1;
  const max = Math.max(...snapshots.map((s) => s.views), 1);
  const pts = snapshots.map((s) => [
    pad + ((new Date(s.captured_at).getTime() - t0) / Math.max(t1 - t0, 1)) * (w - 2 * pad),
    h - pad - (s.views / max) * (h - 2 * pad),
  ]);
  return (
    <div className="rounded-md bg-zinc-900 p-3">
      <div className="mb-1 flex justify-between text-[11px] uppercase tracking-wide text-zinc-500">
        <span>View trajectory</span><span className="tabular-nums">{compact(snapshots[snapshots.length - 1].views)}</span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" role="img" aria-label="Views over time">
        <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke="currentColor" strokeWidth="2" className="text-emerald-400" />
        {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="2.5" className="fill-emerald-400"><title>{`${snapshots[i].age_bucket ?? ""} ${compact(snapshots[i].views)}`}</title></circle>)}
      </svg>
    </div>
  );
}
