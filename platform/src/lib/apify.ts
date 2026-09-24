// Apify orchestration: actor selection, run kickoff, dataset fetch, and
// normalization of each actor's item shape into one VideoRecord.
import { env } from "./env";

export type Platform = "tiktok" | "instagram" | "youtube";

export const ACTORS: Record<Platform, string> = {
  tiktok: process.env.APIFY_TIKTOK_ACTOR ?? "clockworks~tiktok-scraper",
  instagram: process.env.APIFY_INSTAGRAM_ACTOR ?? "apify~instagram-reel-scraper",
  youtube: process.env.APIFY_YOUTUBE_ACTOR ?? "streamers~youtube-shorts-scraper",
};

export interface VideoRecord {
  platform: Platform;
  handle: string;
  followerCount: number | null;
  externalId: string;
  videoUrl: string;
  mediaUrl: string | null;
  thumbnailUrl: string | null;
  caption: string | null;
  audioId: string | null;
  durationSeconds: number | null;
  publishedAt: string | null;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
}

/** Actor input for an incremental pull of `handles` (latest `perProfile` posts each). */
export function actorInput(platform: Platform, handles: string[], perProfile = 30): Record<string, unknown> {
  switch (platform) {
    case "tiktok":
      return {
        profiles: handles,
        resultsPerPage: perProfile,
        shouldDownloadVideos: false,
        shouldDownloadCovers: false,
        proxyConfiguration: { useApifyProxy: true },
      };
    case "instagram":
      return { username: handles, resultsLimit: perProfile, proxyConfiguration: { useApifyProxy: true } };
    case "youtube":
      return { channels: handles.map((h) => (h.startsWith("@") ? h : `@${h}`)), maxResultsShorts: perProfile };
  }
}

/** Start an actor run; Apify calls our webhook on success with the dataset id. */
export async function startActorRun(platform: Platform, handles: string[]): Promise<{ runId: string }> {
  const webhook = [
    {
      eventTypes: ["ACTOR.RUN.SUCCEEDED"],
      requestUrl: `${env.appUrl()}/api/webhooks/apify?platform=${platform}`,
      headersTemplate: JSON.stringify({ "x-webhook-secret": env.apifyWebhookSecret() }),
      payloadTemplate: `{"runId": {{resource.id}}, "datasetId": {{resource.defaultDatasetId}}, "status": {{resource.status}}}`,
    },
  ];
  const url = new URL(`https://api.apify.com/v2/acts/${ACTORS[platform]}/runs`);
  url.searchParams.set("webhooks", Buffer.from(JSON.stringify(webhook)).toString("base64"));
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.apifyToken()}`, "Content-Type": "application/json" },
    body: JSON.stringify(actorInput(platform, handles)),
  });
  if (!res.ok) throw new Error(`Apify run start failed (${res.status}): ${await res.text()}`);
  const json = (await res.json()) as { data: { id: string } };
  return { runId: json.data.id };
}

export async function fetchDataset(datasetId: string): Promise<unknown[]> {
  const items: unknown[] = [];
  const pageSize = 1000;
  for (let offset = 0; ; offset += pageSize) {
    const url = `https://api.apify.com/v2/datasets/${datasetId}/items?clean=true&offset=${offset}&limit=${pageSize}`;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${env.apifyToken()}` } });
    if (!res.ok) throw new Error(`Apify dataset fetch failed (${res.status})`);
    const page = (await res.json()) as unknown[];
    items.push(...page);
    if (page.length < pageSize) return items;
  }
}

// ---------------------------------------------------------------------------
// Normalization
// ---------------------------------------------------------------------------

type Item = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

const num = (...vals: unknown[]): number => {
  for (const v of vals) {
    const n = typeof v === "string" ? Number(v.replace(/,/g, "")) : v;
    if (typeof n === "number" && Number.isFinite(n)) return n;
  }
  return 0;
};
const numOrNull = (...vals: unknown[]): number | null => {
  const n = num(...vals, NaN);
  return n === 0 && vals.every((v) => v == null) ? null : n;
};
const str = (...vals: unknown[]): string | null => {
  for (const v of vals) if (typeof v === "string" && v.length) return v;
  return null;
};
const iso = (v: unknown): string | null => {
  if (v == null || v === "") return null;
  const d = typeof v === "number" ? new Date(v < 1e12 ? v * 1000 : v) : new Date(String(v));
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
};

/** "1:02" / "PT1M2S" / 62 -> 62 */
export function parseDuration(v: unknown): number | null {
  if (typeof v === "number") return v;
  if (typeof v !== "string" || !v) return null;
  const iso8601 = v.match(/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$/);
  if (iso8601) return num(iso8601[1]) * 3600 + num(iso8601[2]) * 60 + num(iso8601[3]);
  const parts = v.split(":").map(Number);
  if (parts.some(Number.isNaN)) return null;
  return parts.reduce((acc, p) => acc * 60 + p, 0);
}

export function normalizeTikTok(it: Item): VideoRecord | null {
  const id = str(it.id, String(it.id ?? ""));
  const handle = str(it.authorMeta?.name, it["authorMeta.name"]);
  if (!id || !handle) return null;
  return {
    platform: "tiktok",
    handle,
    followerCount: numOrNull(it.authorMeta?.fans),
    externalId: id,
    videoUrl: str(it.webVideoUrl) ?? `https://www.tiktok.com/@${handle}/video/${id}`,
    mediaUrl: str(it.mediaUrls?.[0], it.videoMeta?.downloadAddr, it.videoMeta?.playAddr),
    thumbnailUrl: str(it.videoMeta?.coverUrl, it.videoMeta?.originalCoverUrl),
    caption: str(it.text),
    audioId: str(it.musicMeta?.musicId, it.musicMeta?.musicId?.toString()),
    durationSeconds: numOrNull(it.videoMeta?.duration),
    publishedAt: iso(it.createTimeISO ?? it.createTime),
    views: num(it.playCount),
    likes: num(it.diggCount),
    comments: num(it.commentCount),
    shares: num(it.shareCount),
    saves: num(it.collectCount),
  };
}

export function normalizeInstagram(it: Item): VideoRecord | null {
  const id = str(it.shortCode, it.id);
  const handle = str(it.ownerUsername);
  if (!id || !handle) return null;
  return {
    platform: "instagram",
    handle,
    followerCount: numOrNull(it.ownerFollowersCount, it.followersCount),
    externalId: id,
    videoUrl: str(it.url) ?? `https://www.instagram.com/reel/${id}/`,
    mediaUrl: str(it.videoUrl),
    thumbnailUrl: str(it.displayUrl),
    caption: str(it.caption),
    audioId: str(it.musicInfo?.audio_id),
    durationSeconds: numOrNull(it.videoDuration),
    publishedAt: iso(it.timestamp),
    views: num(it.videoPlayCount, it.videoViewCount, it.playsCount),
    likes: num(it.likesCount),
    comments: num(it.commentsCount),
    shares: num(it.sharesCount, it.reshareCount),
    saves: num(it.savesCount),
  };
}

export function normalizeYouTube(it: Item): VideoRecord | null {
  const id = str(it.id);
  const handle = str(it.channelUsername, it.channelName, it.input)?.replace(/^@/, "") ?? null;
  if (!id || !handle) return null;
  return {
    platform: "youtube",
    handle,
    followerCount: numOrNull(it.numberOfSubscribers, it.subscriberCount),
    externalId: id,
    videoUrl: str(it.url) ?? `https://www.youtube.com/shorts/${id}`,
    mediaUrl: null, // YouTube serves no direct CDN URL; the media worker resolves via yt-dlp
    thumbnailUrl: str(it.thumbnailUrl) ?? `https://i.ytimg.com/vi/${id}/hqdefault.jpg`,
    caption: str(it.title, it.text),
    audioId: null,
    durationSeconds: parseDuration(it.duration),
    publishedAt: iso(it.date ?? it.uploadDate),
    views: num(it.viewCount),
    likes: num(it.likes, it.likeCount),
    comments: num(it.commentsCount, it.commentCount),
    shares: 0,
    saves: 0,
  };
}

export function normalize(platform: Platform, items: unknown[]): VideoRecord[] {
  const fn = { tiktok: normalizeTikTok, instagram: normalizeInstagram, youtube: normalizeYouTube }[platform];
  return items.map((i) => fn(i as Item)).filter((r): r is VideoRecord => r !== null);
}
