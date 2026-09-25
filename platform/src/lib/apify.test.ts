import { describe, expect, it } from "vitest";
import { actorInput, normalize, parseDuration } from "./apify";

describe("normalize", () => {
  it("maps clockworks/tiktok-scraper items", () => {
    const [r] = normalize("tiktok", [
      {
        id: "7300000000000000001",
        text: "Stop writing blog posts",
        createTimeISO: "2026-09-01T10:00:00.000Z",
        authorMeta: { name: "growthguy", fans: 3100 },
        playCount: 100000, diggCount: 9000, commentCount: 400, shareCount: 1200, collectCount: 2500,
        videoMeta: { duration: 48, coverUrl: "https://cdn/cover.jpg" },
        mediaUrls: ["https://cdn/v.mp4"],
        musicMeta: { musicId: "123" },
        webVideoUrl: "https://www.tiktok.com/@growthguy/video/7300000000000000001",
      },
    ]);
    expect(r).toMatchObject({
      platform: "tiktok", handle: "growthguy", followerCount: 3100, views: 100000,
      saves: 2500, shares: 1200, mediaUrl: "https://cdn/v.mp4", durationSeconds: 48,
      publishedAt: "2026-09-01T10:00:00.000Z",
    });
  });

  it("maps instagram reels and youtube shorts", () => {
    const [ig] = normalize("instagram", [
      { shortCode: "Cabc", ownerUsername: "brand", videoPlayCount: 5000, likesCount: 300, commentsCount: 12,
        timestamp: "2026-09-02T00:00:00Z", videoUrl: "https://cdn/r.mp4", caption: "hi" },
    ]);
    expect(ig).toMatchObject({ platform: "instagram", externalId: "Cabc", views: 5000, saves: 0 });
    const [yt] = normalize("youtube", [
      { id: "abc123", title: "Short", channelUsername: "@chan", viewCount: "12,000", duration: "0:45", date: "2026-09-03" },
    ]);
    expect(yt).toMatchObject({ platform: "youtube", handle: "chan", views: 12000, durationSeconds: 45, mediaUrl: null });
  });

  it("drops items without an id or author", () => {
    expect(normalize("tiktok", [{ text: "x" }])).toEqual([]);
  });

  it("maps long-form YouTube videos and ignores non-video actor rows", () => {
    const records = normalize("youtube_long", [
      {
        type: "video", scrapeVideoType: "long", id: "long123", title: "An investigation",
        channelUsername: "@fern-tv", numberOfSubscribers: 5_520_000,
        viewCount: 4_000_000, likes: 75_000, commentsCount: 4_500,
        durationSeconds: 1_691, date: "2026-09-02T17:00:00Z",
      },
      { input: "@missing", error: "NO_VIDEOS" },
      { type: "video", scrapeVideoType: "short", id: "short123", channelUsername: "@fern-tv" },
      { type: "video", id: "short456", url: "https://www.youtube.com/shorts/short456", channelUsername: "@fern-tv" },
    ]);
    expect(records).toHaveLength(1);
    expect(records[0]).toMatchObject({
      platform: "youtube_long", handle: "fern-tv", externalId: "long123",
      videoUrl: "https://www.youtube.com/watch?v=long123", followerCount: 5_520_000,
      views: 4_000_000, likes: 75_000, comments: 4_500,
      durationSeconds: 1_691, publishedAt: "2026-09-02T17:00:00.000Z",
    });
  });
});

describe("actorInput", () => {
  it("requests recent regular YouTube uploads separately from Shorts", () => {
    expect(actorInput("youtube_long", ["fern-tv", "@another"], 30)).toEqual({
      channelUrls: ["https://www.youtube.com/@fern-tv", "https://www.youtube.com/@another"],
      maxResults: 30,
      videoType: "long",
      sortOrder: "latest",
    });
    expect(actorInput("youtube", ["fern-tv"], 30)).toMatchObject({ maxResultsShorts: 30 });
  });
});

describe("parseDuration", () => {
  it("parses clock and ISO-8601 formats", () => {
    expect(parseDuration("1:02")).toBe(62);
    expect(parseDuration("PT1M2S")).toBe(62);
    expect(parseDuration(30)).toBe(30);
    expect(parseDuration("")).toBeNull();
  });
});
