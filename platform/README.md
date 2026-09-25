# Competitor Intel

A competitor content-intelligence platform for TikTok, Instagram Reels, YouTube Shorts, and regular YouTube videos. It pulls in competitor posts, scores each one against its creator's own baseline, breaks the video down with a multimodal model (transcript plus hook frames plus scene cuts), and turns what it finds into a dashboard and a "Remix for my brand" script generator. YouTube Shorts (`youtube`) and regular videos (`youtube_long`) are tracked as separate platforms, so their creator baselines do not mix.

```
Apify actors ──(cron 6h)──► webhook ──► ingest: upsert → snapshot → rescore (median of last 20)
                                              │  OM ≥ ANALYZE_MIN_MULTIPLIER or OM ≥ 2.5 (outlier)
                                              ▼
                        process-video (Inngest, concurrency-limited)
             download (CDN URL → yt-dlp fallback) → ffmpeg hook frames 0.5/1.5/3.0s + scene cuts
             → Deepgram Nova-3 (word timestamps + sentiment) → Claude structured output
             → OpenAI embeddings (hook + content, 1536-d) → Supabase / pgvector
                                              ▼
            Next.js dashboard: Outlier Feed · Video Drawer · Pattern Matrix · Semantic Search
                               Remix Studio · Weekly Digest (Monday cron) · Competitors
```

## Where each piece lives

| Spec layer | Code |
|---|---|
| 1. Ingestion (Apify) | `src/lib/apify.ts` (actor inputs, run with webhook, dataset paging, per-actor normalization), `src/app/api/webhooks/apify/route.ts`, `scheduleIngest` / `ingestDataset` in `src/inngest/functions.ts` |
| Outlier scoring | `src/lib/scoring.ts` (tested) and the SQL function `recompute_competitor_baseline` (runs after every batch) |
| 2. Media and transcription | `src/lib/media/download.ts`, `frames.ts` (ffmpeg hook frames, scene-cut detection, cut rate), `watch.ts` (watch skill scene evidence), `transcribe.ts` (Deepgram Nova-3) |
| 3. Multimodal analysis | `src/lib/schema.ts` (Zod schema with closed archetype, beat and CTA taxonomies), `src/lib/llm/analyze.ts` (overview), `src/lib/llm/frame.ts` (FRAME), `src/lib/frame-windows.ts` (five-second scene limit), `src/lib/pacing.ts` (WPM is measured, not guessed) |
| 4. Data layer | `supabase/migrations/0001_init.sql` and `0002_youtube_long.sql`: the spec's three tables plus metric snapshots, brand profiles, remix scripts, digests, HNSW indexes, and the RPCs `match_videos`, `similar_hooks`, `archetype_matrix` and the view `outlier_feed` |
| 5. Dashboard | `src/app/*`, `src/components/*` (Next.js App Router, Tailwind v4, TanStack Table) |
| Phase 4 synthesis | `src/lib/llm/remix.ts` (keeps beat timings; each beat gets a word budget of WPM × duration), `src/lib/llm/digest.ts` |

### Scoring

```
OM = views / median(views of creator's last 20 videos)          → is_outlier when OM ≥ 2.5
ER = (likes + 2·comments + 3·saves + 4·shares) / views × 100
```

The baseline is recomputed in Postgres after each ingest batch, and every video from that creator is rescored. Each scrape also writes a row to `video_metric_snapshots`, tagged `ingest`, `d1`, `d3` or `d7` by the video's age. With the default 6-hour cadence, those rows record how fast each video's views level off. A video that was below the analysis bar (`skipped`) is queued for analysis once its multiplier later crosses the bar.

### Analysis design choices

- **The model reads frames as well as the transcript.** The overview uses three hook frames and up to 12 scene-cut frames with the timestamped Deepgram transcript. The FRAME pass invokes the sibling watch skill in balanced mode on the downloaded video. It pins visual evidence inside every five-second window, adds scene-aware frames, and analyzes consecutive windows in one-minute batches.
- **The video drawer has a FRAME tab.** Every scene lasts at most five seconds and describes Figure, Room, Action, Movement, and Extras, including an analyst-observed character block and a continuity “don't-line.” Window boundaries are set in code and checked before storage. The creator's original character prompt is not available from video frames; unverified sound or camera movement is labeled as such. Earlier analyses without FRAME data keep their Breakdown view and show an empty FRAME state.
- **Archetypes, beat types and CTA types are fixed lists (enums).** If the model could name archetypes freely, the Pattern Matrix would split into near-duplicates ("Contrarian take" vs "Hot take").
- **Pacing is measured, not asked of the model.** Words per minute comes from Deepgram word timestamps and cuts per minute from ffmpeg scene detection. The measured WPM replaces whatever number the model returns.
- Claude calls use structured outputs (`messages.parse` + Zod), adaptive thinking, and server-side refusal fallbacks (`fallbacks: "default"`). The default model is `claude-opus-5`; set `ANALYSIS_MODEL` to change it.
- Embeddings use OpenAI `text-embedding-3-small` (1536-d, matching the spec's `vector(1536)`), because Anthropic has no embeddings endpoint.

## Quick start (Docker, one command)

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), then:

```bash
cd platform
docker compose up --build
```

Open http://localhost:3000 for the dashboard (with demo data) and http://localhost:8288 for the Inngest dashboard, where you can watch background jobs. The first build takes a few minutes. Stop with `Ctrl+C`. `docker compose down -v` wipes the database.

This runs everything locally: Postgres + pgvector, loaded with the schema and demo data; PostgREST behind a Supabase-style gateway; the Inngest dev server; and the app, which bundles ffmpeg, yt-dlp, and the sibling `skills/watch` scripts. You don't need a Supabase account. Keyframe images aren't stored locally because there's no storage service, but the analysis still uses them.

To scrape and analyze real competitors, copy `.env.example` to `.env` and fill in `APIFY_TOKEN`, `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`, then rerun the command. Apify's webhook needs a public URL, so set `APP_URL` to a tunnel (e.g. `ngrok http 3000`), or POST scraped items straight to the webhook as shown below. The local webhook secret is `local-webhook-secret` unless you set `APIFY_WEBHOOK_SECRET`.

## Setup (Supabase)

```bash
cd platform
npm install
cp .env.example .env.local        # fill in keys

# Database: Supabase project with pgvector
supabase db push                  # or run both migration files in order in the SQL editor
psql "$DATABASE_URL" -f supabase/seed.sql   # optional demo data

npm run dev                       # dashboard on :3000
npm run inngest:dev               # Inngest dev server (set INNGEST_DEV=1)
```

For local development, the watch skill lives at `../skills/watch` relative to `platform/`; set `WATCH_SKILL_DIR` only if it lives elsewhere. The container sets `WATCH_SKILL_DIR=/app/skills/watch` and uses a named Docker build context for those scripts. A direct image build from `platform/` needs `docker build --build-context watch_skill=../skills/watch -f Dockerfile .` (Docker BuildKit required). `docker compose up --build` supplies that context automatically.

Add competitors on `/competitors`, then click **Run ingest now** or wait for the cron. For local webhooks, Apify has to be able to reach `APP_URL`, so use a tunnel. You can also POST a batch straight to the webhook:

Choose **YouTube Long** to track regular channel uploads separately from **YouTube Shorts**. Long uploads use the [Grow Media YouTube channel video actor](https://apify.com/grow_media/youtube-channel-video-scraper) with `videoType: "long"`, latest-first sorting, and one channel per run so the 30-video limit applies to each channel. Set `APIFY_YOUTUBE_LONG_ACTOR` to override the actor. The long-video media worker downloads at up to 720p and allows longer download/FFmpeg jobs.

```bash
curl -X POST "localhost:3000/api/webhooks/apify?platform=tiktok" \
  -H "x-webhook-secret: $APIFY_WEBHOOK_SECRET" -H "content-type: application/json" \
  -d '{"items": [ ...raw clockworks/tiktok-scraper items... ]}'
```

### Deploying

The worker runs `ffmpeg`, `ffprobe`, `yt-dlp`, and the bundled watch scripts, so deploy the included `Dockerfile` to a container host. Build with the named `watch_skill` context shown above, then push the image to your host. Pure serverless won't work for it. Register `https://<host>/api/inngest` with Inngest Cloud. The dashboard, API routes and workers all run from the same image. `DASHBOARD_PASSWORD` turns on basic auth for the UI. The webhook and the Inngest endpoint authenticate with their own secrets.

## Tests

```bash
npm test          # scoring, Apify normalization, Deepgram parsing, pacing, ffmpeg keyframes (skipped without ffmpeg)
npm run typecheck
npm run build
```

## Known limits

- The YouTube scrapers don't return shares or saves, so ER for both Shorts and long videos counts only likes and comments. YouTube also has no CDN URL here, so the worker downloads videos with yt-dlp.
- The YouTube Long actor is community maintained. Its output includes per-video dates and engagement counts in the documented format, but live scrape behavior depends on that external actor. Long videos take more time and compute to download, transcribe, and analyze.
- Instagram reel items often leave out saves and shares, which lowers ER compared with TikTok. Compare ER within a platform, not across platforms.
- Day 1/3/7 snapshots rely on the regular profile scrape (the last 30 posts per creator). A creator who posts more than 30 times in 7 days drops out of the d7 window. If that matters, add a per-URL refresh actor run.
- CDN URLs expire. The drawer falls back to linking to the original post, and keyframes are stored in Supabase Storage so they stay available.
