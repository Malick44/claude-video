"use client";

import { useEffect, useRef, useState } from "react";
import { parseRange } from "@/lib/pacing";
import type { VideoIntelligence } from "@/lib/schema";

type Scenes = NonNullable<VideoIntelligence["frame_analysis"]>;

interface FrameSceneNavigatorProps {
  scenes: Scenes;
  meta?: VideoIntelligence["frame_analysis_meta"];
  time: number;
  canSeek: boolean;
  onSeek: (time: number) => void;
}

/** A scene is selected for reading independently of the player's current position. */
export function FrameSceneNavigator({ scenes, meta, time, canSeek, onSeek }: FrameSceneNavigatorProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const railRef = useRef<HTMLOListElement>(null);
  const sceneRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const sceneHeadingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => setSelectedIndex(0), [scenes]);

  useEffect(() => {
    const rail = railRef.current;
    const button = sceneRefs.current[selectedIndex];
    if (!rail || !button) return;
    const left = button.offsetLeft - rail.offsetLeft;
    const right = left + button.offsetWidth;
    if (left < rail.scrollLeft) rail.scrollTo({ left: Math.max(0, left - 8) });
    if (right > rail.scrollLeft + rail.clientWidth) rail.scrollTo({ left: right - rail.clientWidth + 8 });
  }, [selectedIndex]);

  if (!scenes.length) {
    return (
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h3 className="text-sm font-semibold text-zinc-100">No FRAME scenes yet</h3>
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">This video has no scene-level FRAME analysis. Its beat timeline is available in Breakdown.</p>
      </section>
    );
  }

  const safeIndex = Math.min(selectedIndex, scenes.length - 1);
  const selected = scenes[safeIndex];
  const selectedRange = parseRange(selected.timestamp_range);
  const playerIndex = canSeek ? scenes.findIndex((scene, index) => {
    const range = parseRange(scene.timestamp_range);
    return range && time >= range[0] && (time < range[1] || (index === scenes.length - 1 && time <= range[1]));
  }) : -1;
  const stepToScene = (index: number) => {
    setSelectedIndex(index);
    window.requestAnimationFrame(() => sceneHeadingRef.current?.focus());
  };

  return (
    <div className="space-y-4">
      <header className="space-y-2">
        <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-zinc-200">FRAME scenes</h3>
              {meta?.source === "watch" && <span className="rounded-full border border-fuchsia-500/40 bg-fuchsia-500/10 px-2 py-0.5 text-[11px] font-medium text-fuchsia-200">Watch frames · ≤5s</span>}
            </div>
            <p className="mt-1 text-xs text-zinc-500">Select a scene to read its Figure, Room, Action, Movement, and Extras.</p>
          </div>
          <span className="font-mono text-xs tabular-nums text-zinc-400" aria-live="polite">Scene {safeIndex + 1} of {scenes.length}</span>
        </div>
        <p className="text-xs leading-relaxed text-zinc-500">Character blocks use the analyst&apos;s exact observed wording. The creator&apos;s original prompt is unavailable; sound and camera details are limited to the evidence.</p>
      </header>

      <nav aria-label="FRAME scenes" className="relative">
        <ol ref={railRef} className="flex snap-x gap-2 overflow-x-auto pb-2" style={{ scrollbarGutter: "stable" }}>
          {scenes.map((scene, index) => {
            const isSelected = index === safeIndex;
            const atPlayer = index === playerIndex;
            return (
              <li key={`${index}-${scene.timestamp_range}`} className="min-w-0 shrink-0 snap-start">
                <button
                  ref={(node) => { sceneRefs.current[index] = node; }}
                  type="button"
                  onClick={() => setSelectedIndex(index)}
                  aria-current={isSelected ? "step" : undefined}
                  aria-label={`View scene ${index + 1} of ${scenes.length}, ${scene.timestamp_range}${atPlayer ? ", at player position" : ""}`}
                  className={`relative flex min-w-[116px] flex-col gap-1 rounded-md border px-3 py-2 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fuchsia-400 ${isSelected ? "border-fuchsia-400/80 bg-fuchsia-500/10 text-zinc-100" : "border-zinc-800 bg-zinc-900/70 text-zinc-400 hover:border-zinc-600 hover:bg-zinc-800/80"}`}
                >
                  <span className="flex w-full items-center justify-between gap-2 text-[11px] font-semibold uppercase tracking-wide">
                    <span>Scene {String(index + 1).padStart(2, "0")}</span>
                    {atPlayer && <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />}
                  </span>
                  <span className={`font-mono text-[11px] tabular-nums ${isSelected ? "text-fuchsia-200" : "text-zinc-500"}`}>{scene.timestamp_range}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      {canSeek && playerIndex >= 0 && playerIndex !== safeIndex && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-emerald-900/40 bg-emerald-950/15 px-3 py-2 text-xs text-zinc-400">
          <span><span aria-hidden="true" className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 align-middle" />Player position: scene {playerIndex + 1}</span>
          <button type="button" onClick={() => setSelectedIndex(playerIndex)} className="rounded px-2 py-1 font-medium text-emerald-300 hover:bg-emerald-500/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400">View that scene</button>
        </div>
      )}

      <article className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/60">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 px-4 py-3">
          <div className="flex items-baseline gap-3">
            <h4 ref={sceneHeadingRef} tabIndex={-1} className="text-base font-semibold text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400">Scene {String(safeIndex + 1).padStart(2, "0")}</h4>
            <span className="font-mono text-xs tabular-nums text-zinc-400">{selected.timestamp_range}</span>
          </div>
          {canSeek && selectedRange && (
            <button type="button" onClick={() => onSeek(selectedRange[0])} className="rounded-md border border-fuchsia-500/40 bg-fuchsia-500/10 px-2.5 py-1.5 text-xs font-medium text-fuchsia-200 hover:bg-fuchsia-500/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fuchsia-400" aria-label={`Play scene ${safeIndex + 1} from ${selected.timestamp_range.split(/\s*[-–]\s*/)[0]}`}>
              Play from start ↗
            </button>
          )}
        </div>
        <div className="divide-y divide-zinc-800/70 px-4">
          <FrameField letter="F" title="Figure" value={selected.figure}>
            <div className="mt-3 rounded-md border border-zinc-700/70 bg-zinc-950/70 p-3">
              <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Character block · analyst wording</div>
              <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-zinc-200">{selected.character_block || "No reusable character block applies to this scene."}</p>
            </div>
          </FrameField>
          <FrameField letter="R" title="Room" value={selected.room} />
          <FrameField letter="A" title="Action" value={selected.action} />
          <FrameField letter="M" title="Movement" value={selected.movement} />
          <FrameField letter="E" title="Extras" value={selected.extras}>
            <div className="mt-3 rounded-md border border-amber-900/60 bg-amber-950/20 p-3">
              <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-amber-400">Don&apos;t-line · recreation guidance</div>
              <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-amber-100">{selected.dont_line || "Not documented in the available analysis."}</p>
            </div>
          </FrameField>
        </div>
      </article>

      <div className="flex items-center justify-between gap-3" aria-label="Scene navigation">
        <button type="button" disabled={safeIndex === 0} onClick={() => stepToScene(safeIndex - 1)} className="rounded-md border border-zinc-800 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400">← Previous</button>
        <span className="font-mono text-xs tabular-nums text-zinc-500">{safeIndex + 1} / {scenes.length}</span>
        <button type="button" disabled={safeIndex === scenes.length - 1} onClick={() => stepToScene(safeIndex + 1)} className="rounded-md border border-zinc-800 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fuchsia-400">Next →</button>
      </div>
    </div>
  );
}

function FrameField({ letter, title, value, children }: { letter: string; title: string; value: string; children?: React.ReactNode }) {
  return (
    <section className="grid grid-cols-[1.75rem_1fr] gap-2 py-3" aria-label={title}>
      <span aria-hidden="true" className="flex h-6 w-6 items-center justify-center rounded bg-fuchsia-500/15 text-xs font-bold text-fuchsia-300">{letter}</span>
      <div className="min-w-0">
        <h5 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-400">{title}</h5>
        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-zinc-200">{value || "Not documented in the available analysis."}</p>
        {children}
      </div>
    </section>
  );
}
