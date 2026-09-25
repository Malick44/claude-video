"use client";

import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnFiltersState,
  type SortingState,
} from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { compact, multiplier, omTone, pct, PLATFORM_LABEL, shortDate } from "@/lib/format";
import type { FeedRow } from "@/lib/types";
import { VideoDrawer } from "./VideoDrawer";

const col = createColumnHelper<FeedRow>();

export function OutlierFeed({ rows, window, windows }: { rows: FeedRow[]; window: string; windows: string[] }) {
  const router = useRouter();
  const [sorting, setSorting] = useState<SortingState>([{ id: "outlier_multiplier", desc: true }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [outliersOnly, setOutliersOnly] = useState(false);
  const [view, setView] = useState<"grid" | "table">("grid");
  const [openId, setOpenId] = useState<string | null>(null);

  const data = useMemo(() => (outliersOnly ? rows.filter((r) => r.is_outlier) : rows), [rows, outliersOnly]);
  const archetypes = useMemo(() => [...new Set(rows.map((r) => r.hook_archetype).filter(Boolean))].sort() as string[], [rows]);
  const creators = useMemo(() => [...new Set(rows.map((r) => r.handle))].sort(), [rows]);

  const columns = useMemo(
    () => [
      col.accessor("thumbnail_url", {
        header: "",
        enableSorting: false,
        cell: (c) => (c.getValue() ? <img src={c.getValue()!} alt="" className={`h-16 rounded bg-black ${c.row.original.platform === "youtube_long" ? "w-28 object-contain" : "w-9 object-cover"}`} /> : <div className={`h-16 rounded bg-zinc-800 ${c.row.original.platform === "youtube_long" ? "w-28" : "w-9"}`} />),
      }),
      col.accessor("handle", { header: "Creator", filterFn: "equalsString", cell: (c) => <span className="font-medium">@{c.getValue()}</span> }),
      col.accessor("platform", { header: "Platform", filterFn: "equalsString", cell: (c) => PLATFORM_LABEL[c.getValue()] ?? c.getValue() }),
      col.accessor("outlier_multiplier", {
        header: "Outlier ×",
        sortUndefined: "last",
        cell: (c) => <span className={`rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${omTone(c.getValue())}`}>{multiplier(c.getValue())}</span>,
      }),
      col.accessor("views", { header: "Views", cell: (c) => <span className="tabular-nums">{compact(c.getValue())}</span> }),
      col.accessor("median_views_last_20", { header: "Baseline", cell: (c) => <span className="tabular-nums text-zinc-400">{compact(c.getValue())}</span> }),
      col.accessor("engagement_rate", { header: "ER", cell: (c) => <span className="tabular-nums">{pct(c.getValue())}</span> }),
      col.accessor("saves", { header: "Saves", cell: (c) => <span className="tabular-nums">{compact(c.getValue())}</span> }),
      col.accessor("hook_archetype", { header: "Hook archetype", filterFn: "equalsString", cell: (c) => c.getValue() ?? <Status s={c.row.original.processing_status} /> }),
      col.accessor("hook_text", { header: "Hook", enableSorting: false, cell: (c) => <span className="line-clamp-2 max-w-sm text-zinc-300">{c.getValue() ?? c.row.original.caption}</span> }),
      col.accessor("published_at", { header: "Published", cell: (c) => shortDate(c.getValue()) }),
    ],
    [],
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, globalFilter },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: (row, _id, value: string) => {
      const r = row.original;
      return [r.handle, r.caption, r.hook_text, r.primary_topic_cluster].some((s) => s?.toLowerCase().includes(value.toLowerCase()));
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const setFilter = (id: string, value: string) => table.getColumn(id)?.setFilterValue(value || undefined);
  const visible = table.getRowModel().rows;

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm">
        <input
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Filter by caption, hook, topic…"
          className="w-64 rounded-md border border-zinc-700 bg-zinc-950 px-3 py-1.5 outline-none focus:border-zinc-500"
        />
        <Select label="Platform" onChange={(v) => setFilter("platform", v)} options={Object.entries(PLATFORM_LABEL)} />
        <Select label="Creator" onChange={(v) => setFilter("handle", v)} options={creators.map((c) => [c, `@${c}`])} />
        <Select label="Archetype" onChange={(v) => setFilter("hook_archetype", v)} options={archetypes.map((a) => [a, a])} />
        <select
          value={window}
          onChange={(e) => router.push(`/?window=${e.target.value}`)}
          className="rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5"
          aria-label="Date window"
        >
          {windows.map((w) => (
            <option key={w} value={w}>{w === "all" ? "All time" : `Last ${w}`}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 px-2 text-zinc-300">
          <input type="checkbox" checked={outliersOnly} onChange={(e) => setOutliersOnly(e.target.checked)} />
          Viral outliers only (≥2.5×)
        </label>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-zinc-500">{visible.length} videos</span>
          <div className="flex rounded-md border border-zinc-700 p-0.5">
            {(["grid", "table"] as const).map((v) => (
              <button key={v} onClick={() => setView(v)} className={`rounded px-2.5 py-1 capitalize ${view === v ? "bg-zinc-700 text-white" : "text-zinc-400"}`}>
                {v}
              </button>
            ))}
          </div>
        </div>
      </div>

      {view === "grid" ? (
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {visible.map(({ original: r }) => (
            <button key={r.id} onClick={() => setOpenId(r.id)} className="group flex flex-col overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900 text-left transition hover:border-zinc-600">
              <div className={`relative bg-zinc-800 ${r.platform === "youtube_long" ? "aspect-video" : "aspect-[9/16]"}`}>
                {r.thumbnail_url && <img src={r.thumbnail_url} alt="" className={`h-full w-full ${r.platform === "youtube_long" ? "object-contain" : "object-cover"}`} loading="lazy" />}
                <span className={`absolute left-2 top-2 rounded-full px-2 py-0.5 text-sm font-bold tabular-nums backdrop-blur ${omTone(r.outlier_multiplier)}`}>
                  {multiplier(r.outlier_multiplier)}
                </span>
                <span className="absolute right-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wide">{PLATFORM_LABEL[r.platform]}</span>
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-2 pt-8 text-xs">
                  <div className="font-medium">@{r.handle}</div>
                  <div className="tabular-nums text-zinc-300">
                    {compact(r.views)} views · baseline {compact(r.median_views_last_20)}
                  </div>
                </div>
              </div>
              <div className="space-y-1 p-2 text-xs">
                <div className="truncate text-zinc-400">{r.hook_archetype ?? <Status s={r.processing_status} />}</div>
                <div className="line-clamp-2 text-zinc-200">{r.hook_text ?? r.caption}</div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="mt-4 overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-left text-xs uppercase tracking-wide text-zinc-400">
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((h) => (
                    <th key={h.id} className="whitespace-nowrap px-3 py-2">
                      {h.column.getCanSort() ? (
                        <button onClick={h.column.getToggleSortingHandler()} className="hover:text-white">
                          {flexRender(h.column.columnDef.header, h.getContext())}
                          {{ asc: " ▲", desc: " ▼" }[h.column.getIsSorted() as string] ?? ""}
                        </button>
                      ) : (
                        flexRender(h.column.columnDef.header, h.getContext())
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.id} onClick={() => setOpenId(row.original.id)} className="cursor-pointer border-t border-zinc-800 hover:bg-zinc-900">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2 align-middle">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {visible.length === 0 && <p className="mt-10 text-center text-zinc-500">No videos match. Add competitors and run an ingest.</p>}

      <VideoDrawer videoId={openId} onClose={() => setOpenId(null)} />
    </>
  );
}

function Select({ label, options, onChange }: { label: string; options: [string, string][]; onChange: (v: string) => void }) {
  return (
    <select onChange={(e) => onChange(e.target.value)} className="max-w-48 rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5" aria-label={label}>
      <option value="">All {label.toLowerCase()}s</option>
      {options.map(([v, l]) => (
        <option key={v} value={v}>{l}</option>
      ))}
    </select>
  );
}

function Status({ s }: { s: string }) {
  const label = { pending: "Queued", processing: "Analyzing…", failed: "Analysis failed", skipped: "Not analyzed", done: "—" }[s] ?? s;
  return <span className="italic text-zinc-500">{label}</span>;
}
