import { db } from "@/lib/db";
import type { Digest } from "@/lib/schema";
import { DigestTrigger } from "@/components/Triggers";

export const dynamic = "force-dynamic";

export default async function DigestsPage() {
  const { data } = await db().from("weekly_digests").select("week_start, digest_json, created_at").order("week_start", { ascending: false }).limit(8);
  const digests = (data ?? []) as { week_start: string; digest_json: Digest }[];
  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Weekly Digest</h1>
          <p className="text-sm text-zinc-400">Generated every Monday from the week&apos;s outliers and the archetype matrix.</p>
        </div>
        <DigestTrigger />
      </div>
      {digests.length === 0 && <p className="text-zinc-500">No digests yet.</p>}
      {digests.map(({ week_start, digest_json: d }) => (
        <article key={week_start} className="space-y-4 rounded-lg border border-zinc-800 p-5">
          <div className="text-xs uppercase tracking-wide text-zinc-500">Week of {week_start}</div>
          <h2 className="text-xl font-semibold">{d.headline}</h2>
          <p className="text-zinc-300">{d.summary}</p>
          <section>
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-emerald-400">Rising formats</h3>
            <ul className="space-y-2 text-sm">
              {d.rising_formats.map((f, i) => (
                <li key={i} className="rounded-md bg-zinc-900 p-3"><b>{f.name}</b> — {f.evidence}<div className="mt-1 text-zinc-400">→ {f.recommendation}</div></li>
              ))}
            </ul>
          </section>
          <section>
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-fuchsia-400">Top hooks</h3>
            <ul className="space-y-1 text-sm">{d.top_hooks.map((h, i) => <li key={i}>“{h.hook}” <span className="text-zinc-400">— {h.why_it_worked}</span></li>)}</ul>
          </section>
          <div className="grid gap-4 text-sm sm:grid-cols-2">
            <section><h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-zinc-400">Fading</h3><ul className="list-disc pl-5">{d.fading_patterns.map((p, i) => <li key={i}>{p}</li>)}</ul></section>
            <section><h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-zinc-400">Experiments to run</h3><ul className="list-disc pl-5">{d.experiments_to_run.map((p, i) => <li key={i}>{p}</li>)}</ul></section>
          </div>
        </article>
      ))}
    </div>
  );
}
