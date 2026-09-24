"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Platform } from "@/lib/apify";
import { compact, PLATFORM_LABEL, shortDate } from "@/lib/format";
import { ToggleActive } from "./Triggers";

export interface CompetitorItem {
  id: string;
  platform: Platform;
  handle: string;
  follower_count: number | null;
  median_views_last_20: number | null;
  niche_category: string | null;
  active: boolean;
  last_scraped_at: string | null;
}

export function CompetitorTable({ rows }: { rows: CompetitorItem[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-sm">
        <thead className="bg-zinc-900 text-left text-xs uppercase tracking-wide text-zinc-400">
          <tr>
            <th className="px-3 py-2">Handle</th>
            <th className="px-3 py-2">Platform</th>
            <th className="px-3 py-2">Niche</th>
            <th className="px-3 py-2 text-right">Followers</th>
            <th className="px-3 py-2 text-right">Baseline views</th>
            <th className="px-3 py-2">Last scraped</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <CompetitorRow key={c.id} item={c} />
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={8} className="px-3 py-10 text-center text-zinc-500">
                No competitors yet — add one above.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function CompetitorRow({ item }: { item: CompetitorItem }) {
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<{ platform: Platform; handle: string; niche: string }>({
    platform: item.platform,
    handle: item.handle,
    niche: item.niche_category ?? "",
  });

  const handleSave = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/competitors", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: item.id,
          platform: form.platform,
          handle: form.handle,
          niche: form.niche,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.error || "Failed to update");
        setSubmitting(false);
        return;
      }
      setIsEditing(false);
      setSubmitting(false);
      router.refresh();
    } catch {
      setError("Network error");
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/competitors?id=${item.id}`, { method: "DELETE" });
      if (!res.ok) {
        const data = await res.json();
        setError(data.error || "Failed to delete");
        setSubmitting(false);
        return;
      }
      setIsDeleting(false);
      setSubmitting(false);
      router.refresh();
    } catch {
      setError("Network error");
      setSubmitting(false);
    }
  };

  if (isEditing) {
    return (
      <tr className="border-t border-zinc-800 bg-zinc-900/60">
        <td className="px-3 py-2">
          <input
            type="text"
            value={form.handle}
            onChange={(e) => setForm({ ...form, handle: e.target.value })}
            className="w-36 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none"
            placeholder="@handle"
          />
        </td>
        <td className="px-3 py-2">
          <select
            value={form.platform}
            onChange={(e) => setForm({ ...form, platform: e.target.value as Platform })}
            className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none"
          >
            <option value="tiktok">TikTok</option>
            <option value="instagram">Instagram Reels</option>
            <option value="youtube">YouTube Shorts</option>
          </select>
        </td>
        <td className="px-3 py-2">
          <input
            type="text"
            value={form.niche}
            onChange={(e) => setForm({ ...form, niche: e.target.value })}
            className="w-32 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none"
            placeholder="Niche"
          />
        </td>
        <td className="px-3 py-2 text-right tabular-nums text-zinc-500">{compact(item.follower_count)}</td>
        <td className="px-3 py-2 text-right tabular-nums text-zinc-500">{compact(item.median_views_last_20)}</td>
        <td className="px-3 py-2 text-zinc-500">{shortDate(item.last_scraped_at)}</td>
        <td className="px-3 py-2">
          <ToggleActive id={item.id} active={item.active} />
        </td>
        <td className="px-3 py-2 text-right">
          <div className="flex items-center justify-end gap-1.5">
            {error && <span className="mr-2 text-xs text-red-400">{error}</span>}
            <button
              onClick={handleSave}
              disabled={submitting}
              className="rounded bg-white px-2.5 py-1 text-xs font-medium text-black hover:bg-zinc-200 disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => {
                setIsEditing(false);
                setError(null);
                setForm({ platform: item.platform, handle: item.handle, niche: item.niche_category ?? "" });
              }}
              disabled={submitting}
              className="rounded bg-zinc-800 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr className="border-t border-zinc-800 hover:bg-zinc-900/30 transition-colors">
      <td className="px-3 py-2 font-medium">@{item.handle}</td>
      <td className="px-3 py-2">{PLATFORM_LABEL[item.platform] ?? item.platform}</td>
      <td className="px-3 py-2 text-zinc-400">{item.niche_category ?? "—"}</td>
      <td className="px-3 py-2 text-right tabular-nums">{compact(item.follower_count)}</td>
      <td className="px-3 py-2 text-right tabular-nums">{compact(item.median_views_last_20)}</td>
      <td className="px-3 py-2 text-zinc-400">{shortDate(item.last_scraped_at)}</td>
      <td className="px-3 py-2">
        <ToggleActive id={item.id} active={item.active} />
      </td>
      <td className="px-3 py-2 text-right">
        {isDeleting ? (
          <div className="flex items-center justify-end gap-1.5">
            <span className="text-xs text-zinc-400">Delete?</span>
            <button
              onClick={handleDelete}
              disabled={submitting}
              className="rounded bg-red-600/90 px-2 py-0.5 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
            >
              {submitting ? "..." : "Confirm"}
            </button>
            <button
              onClick={() => setIsDeleting(false)}
              disabled={submitting}
              className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400 hover:bg-zinc-700 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-end gap-2">
            {error && <span className="text-xs text-red-400">{error}</span>}
            <button
              onClick={() => setIsEditing(true)}
              className="text-xs text-zinc-400 hover:text-zinc-100 transition-colors"
            >
              Edit
            </button>
            <button
              onClick={() => setIsDeleting(true)}
              className="text-xs text-red-400/80 hover:text-red-300 transition-colors"
            >
              Remove
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}
