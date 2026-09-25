-- Track regular YouTube uploads separately from YouTube Shorts.
ALTER TABLE public.competitors
    DROP CONSTRAINT IF EXISTS competitors_platform_check;

ALTER TABLE public.competitors
    ADD CONSTRAINT competitors_platform_check
    CHECK (platform IN ('tiktok', 'instagram', 'youtube', 'youtube_long'));
