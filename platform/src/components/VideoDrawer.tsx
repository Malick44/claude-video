"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { compact, multiplier, omTone, pct, PLATFORM_LABEL, shortDate } from "@/lib/format";
import { fmtTs, parseRange } from "@/lib/pacing";
import type { VideoIntelligence } from "@/lib/schema";
import { FrameSceneNavigator } from "./FrameSceneNavigator";

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

type DrawerTab = "breakdown" | "frame";

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
  const [activeTab, setActiveTab] = useState<DrawerTab>("breakdown");
  const asideRef = useRef<HTMLElement>(null);
  const mediaRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const breakdownTabRef = useRef<HTMLButtonElement>(null);
  const frameTabRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!videoId) return;
    setDetail(null); setError(null); setTime(0); setVideoFailed(false); setActiveTab("breakdown");
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
    if (videoRef.current) {
      videoRef.current.currentTime = t;
      void videoRef.current.play();
      if (window.matchMedia("(max-width: 767px)").matches) {
        mediaRef.current?.scrollIntoView({ block: "start", behavior: "auto" });
      }
    }
  };

  const a = detail?.intelligence?.analysis_json;
  const v = detail?.video;
  const frameScenes = a?.frame_analysis ?? [];
  const switchTab = (next: DrawerTab) => {
    setActiveTab(next);
    asideRef.current?.scrollTo({ top: 0, behavior: "auto" });
  };
  const onTabKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    let next: DrawerTab | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") next = activeTab === "breakdown" ? "frame" : "breakdown";
    if (event.key === "Home") next = "breakdown";
    if (event.key === "End") next = "frame";
    if (!next) return;
    event.preventDefault();
    switchTab(next);
    (next === "breakdown" ? breakdownTabRef : frameTabRef).current?.focus();
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/60" onClick={onClose}>
      <aside ref={asideRef} role="dialog" aria-modal="true" aria-label="Video analysis" onClick={(e) => e.stopPropagation()} className="h-full w-full max-w-5xl overflow-y-auto border-l border-zinc-800 bg-zinc-950 shadow-2xl">
        <div className="sticky top-0 z-30 border-b border-zinc-800 bg-zinc-950/95 shadow-lg shadow-black/20 backdrop-blur">
          <div className="flex min-h-16 items-center gap-3 px-4 py-2 sm:px-5">
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-zinc-100">{v ? (v.caption?.split("#")[0]?.trim() || `@${v.competitors.handle}`) : "Loading video…"}</div>
              {v && <div className="mt-0.5 truncate text-xs text-zinc-400">@{v.competitors.handle} <span aria-hidden="true">·</span> {PLATFORM_LABEL[v.platform]} <span aria-hidden="true">·</span> {shortDate(v.published_at)}</div>}
            </div>
            {v && <button type="button" onClick={() => mediaRef.current?.scrollIntoView({ block: "start", behavior: "auto" })} className="rounded-md border border-zinc-700 px-2.5 py-1.5 text-xs font-medium text-zinc-200 hover:border-zinc-500 hover:bg-zinc-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400 md:hidden">Video</button>}
            {v && <a href={v.video_url} target="_blank" rel="noreferrer" className="hidden rounded-md px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800 sm:inline-flex">Open original ↗</a>}
            {a && <Link href={`/remix?video=${videoId}`} className="hidden rounded-md bg-fuchsia-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-fuchsia-500 sm:inline-flex">Remix for my brand</Link>}
            <button type="button" onClick={onClose} className="flex h-9 w-9 flex-none items-center justify-center rounded-md text-zinc-300 hover:bg-zinc-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400" aria-label="Close video analysis">✕</button>
          </div>
          {a && <div role="tablist" aria-label="Video analysis views" className="flex items-center gap-1 border-t border-zinc-800/80 px-4 sm:px-5">
            <button ref={breakdownTabRef} id="drawer-breakdown-tab" role="tab" type="button"
              aria-selected={activeTab === "breakdown"} aria-controls="drawer-breakdown-panel" tabIndex={activeTab === "breakdown" ? 0 : -1}
              onClick={() => switchTab("breakdown")} onKeyDown={onTabKeyDown}
              className={`border-b-2 px-3 py-2.5 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400 ${activeTab === "breakdown" ? "border-fuchsia-400 text-white" : "border-transparent text-zinc-400 hover:text-zinc-200"}`}>
              Breakdown
            </button>
            <button ref={frameTabRef} id="drawer-frame-tab" role="tab" type="button"
              aria-selected={activeTab === "frame"} aria-controls="drawer-frame-panel" tabIndex={activeTab === "frame" ? 0 : -1}
              onClick={() => switchTab("frame")} onKeyDown={onTabKeyDown}
              className={`border-b-2 px-3 py-2.5 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400 ${activeTab === "frame" ? "border-fuchsia-400 text-white" : "border-transparent text-zinc-400 hover:text-zinc-200"}`}>
              FRAME
            </button>
            {frameScenes.length > 0 && <span className="ml-auto whitespace-nowrap font-mono text-[11px] text-zinc-500">{frameScenes.length} scenes</span>}
          </div>}
        </div>

        {error && <p className="p-5 text-red-400">{error}</p>}
        {v && (
          <div className="grid gap-6 p-4 md:grid-cols-[300px_minmax(0,1fr)] md:p-5">
            {/* Video follows the analysis on small screens so navigation stays above the fold. */}
            <div ref={mediaRef} className="order-2 min-w-0 scroll-mt-32 space-y-4 md:order-1">
              <div className="flex items-center justify-between gap-3 border-t border-zinc-800 pt-4 md:hidden">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Video &amp; performance</h2>
                <div className="flex items-center gap-3 text-xs">
                  <a href={v.video_url} target="_blank" rel="noreferrer" className="text-zinc-300 underline decoration-zinc-600 underline-offset-4">Original ↗</a>
                  {a && <Link href={`/remix?video=${videoId}`} className="text-fuchsia-300 underline decoration-fuchsia-700 underline-offset-4">Remix</Link>}
                </div>
              </div>
              <div className={`${v.platform === "youtube_long" ? "aspect-video" : "aspect-[9/16]"} overflow-hidden rounded-lg bg-black md:sticky md:top-32`}>
                {v.media_url && !videoFailed ? (
                  <video ref={videoRef} src={v.media_url} poster={v.thumbnail_url ?? undefined} controls playsInline className="h-full w-full"
                    onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)} onError={() => setVideoFailed(true)} />
                ) : (
                  <a href={v.video_url} target="_blank" rel="noreferrer" className="relative block h-full">
                    {v.thumbnail_url && <img src={v.thumbnail_url} alt="" className={`h-full w-full opacity-70 ${v.platform === "youtube_long" ? "object-contain" : "object-cover"}`} />}
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

            {/* Analysis leads on mobile and sits beside the video on desktop. */}
            <div className="order-1 min-w-0 space-y-6 md:order-2">
              {!a ? (
                <div className="rounded-lg border border-zinc-800 p-4 text-sm text-zinc-400">
                  Not analyzed yet ({v.processing_status}). {v.processing_error && <span className="text-red-400">{v.processing_error}</span>}
                  <button onClick={() => fetch("/api/ingest", { method: "POST", body: JSON.stringify({ videoId }) })} className="ml-2 rounded bg-zinc-800 px-2 py-1 text-zinc-200 hover:bg-zinc-700">
                    Analyze now
                  </button>
                </div>
              ) : (
                <>
                  <div id="drawer-breakdown-panel" role="tabpanel" aria-labelledby="drawer-breakdown-tab" tabIndex={activeTab === "breakdown" ? 0 : -1} hidden={activeTab !== "breakdown"} className="space-y-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400">
                      <section className="rounded-lg border border-fuchsia-900/60 bg-fuchsia-950/20 p-4">
                        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                          <span className="rounded-full bg-fuchsia-500/20 px-2 py-0.5 font-medium text-fuchsia-300">{a.hook_analysis.hook_archetype}</span>
                          {detail.intelligence?.model === "manual-review" && <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-zinc-300">Manual review</span>}
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
                  </div>
                  <div id="drawer-frame-panel" role="tabpanel" aria-labelledby="drawer-frame-tab" tabIndex={activeTab === "frame" ? 0 : -1} hidden={activeTab !== "frame"}>
                    <FrameSceneNavigator scenes={frameScenes} meta={a.frame_analysis_meta} time={time} canSeek={Boolean(v.media_url && !videoFailed)} onSeek={seek} />
                  </div>
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
