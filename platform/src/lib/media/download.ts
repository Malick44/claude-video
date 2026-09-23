// Fetch the video to local disk. Prefer the scraped CDN URL (fast, no extra
// scrape); fall back to yt-dlp on the canonical post URL when the CDN link is
// missing (YouTube) or has expired.
import { createWriteStream } from "node:fs";
import { stat } from "node:fs/promises";
import { join } from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { run } from "./exec";

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36";

export async function downloadVideo(opts: { mediaUrl: string | null; videoUrl: string; dir: string }): Promise<string> {
  const out = join(opts.dir, "video.mp4");
  if (opts.mediaUrl) {
    try {
      const res = await fetch(opts.mediaUrl, { headers: { "User-Agent": UA, Referer: opts.videoUrl } });
      if (res.ok && res.body) {
        await pipeline(Readable.fromWeb(res.body as import("node:stream/web").ReadableStream), createWriteStream(out));
        if ((await stat(out)).size > 10_000) return out;
      }
    } catch {
      // fall through to yt-dlp
    }
  }
  await run("yt-dlp", ["-f", "mp4/bestvideo[height<=1080]+bestaudio/best", "--merge-output-format", "mp4", "-o", out, "--no-playlist", "--quiet", opts.videoUrl], 300_000);
  return out;
}
