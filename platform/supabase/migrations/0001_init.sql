-- Competitor content intelligence: core schema.
-- Mirrors the spec (competitors / competitor_videos / video_intelligence) and adds
-- the tables the pipeline needs: metric snapshots (day 1/3/7 half-life tracking),
-- processing state, brand profiles for the Remix Studio, and weekly digests.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- Tracked competitor accounts
-- ---------------------------------------------------------------------------
CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('tiktok', 'instagram', 'youtube')),
    handle VARCHAR(100) NOT NULL,
    display_name TEXT,
    profile_url TEXT,
    follower_count INT,
    median_views_last_20 NUMERIC,
    niche_category VARCHAR(100),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, handle)
);

-- ---------------------------------------------------------------------------
-- Individual scraped videos
-- ---------------------------------------------------------------------------
CREATE TABLE competitor_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    external_video_id VARCHAR(255) NOT NULL,
    video_url TEXT NOT NULL,           -- canonical post URL
    media_url TEXT,                    -- CDN mp4 URL (ephemeral; refreshed on each scrape)
    thumbnail_url TEXT,
    caption TEXT,
    audio_id TEXT,
    duration_seconds NUMERIC,
    published_at TIMESTAMPTZ,
    views BIGINT DEFAULT 0,
    likes BIGINT DEFAULT 0,
    comments BIGINT DEFAULT 0,
    shares BIGINT DEFAULT 0,
    saves BIGINT DEFAULT 0,
    outlier_multiplier NUMERIC(8, 2),
    engagement_rate NUMERIC(8, 2),
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE,
    raw_transcript TEXT,
    transcript_words JSONB,            -- [{word,start,end,confidence,sentiment?}]
    keyframes JSONB,                   -- [{t, kind: 'fixed'|'scene', path|url}]
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processing', 'done', 'failed', 'skipped')),
    processing_error TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, external_video_id)
);

CREATE INDEX competitor_videos_competitor_published_idx
    ON competitor_videos (competitor_id, published_at DESC);
CREATE INDEX competitor_videos_outlier_idx
    ON competitor_videos (outlier_multiplier DESC NULLS LAST);

-- Metric snapshots: captures the viral half-life (day 1 / 3 / 7 refreshes).
CREATE TABLE video_metric_snapshots (
    id BIGSERIAL PRIMARY KEY,
    video_id UUID NOT NULL REFERENCES competitor_videos(id) ON DELETE CASCADE,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    age_bucket VARCHAR(10),            -- 'ingest' | 'd1' | 'd3' | 'd7'
    views BIGINT, likes BIGINT, comments BIGINT, shares BIGINT, saves BIGINT
);
CREATE INDEX video_metric_snapshots_video_idx ON video_metric_snapshots (video_id, captured_at);

-- ---------------------------------------------------------------------------
-- Structured video intelligence (LLM decomposition)
-- ---------------------------------------------------------------------------
CREATE TABLE video_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL UNIQUE REFERENCES competitor_videos(id) ON DELETE CASCADE,
    hook_text TEXT,
    visual_hook_description TEXT,
    hook_archetype VARCHAR(100),
    retention_trigger TEXT,
    cta_type VARCHAR(100),
    loop_mechanic TEXT,
    pacing_wpm NUMERIC,
    primary_topic_cluster VARCHAR(150),
    beats_json JSONB,
    remix_notes JSONB,
    analysis_json JSONB,               -- full structured output, for forward-compat
    model TEXT,
    hook_embedding vector(1536),       -- similarity search across competitor hooks
    content_embedding vector(1536),    -- hook + transcript + topic, for semantic search
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX video_intelligence_archetype_idx ON video_intelligence (hook_archetype);
CREATE INDEX video_intelligence_hook_embedding_idx
    ON video_intelligence USING hnsw (hook_embedding vector_cosine_ops);
CREATE INDEX video_intelligence_content_embedding_idx
    ON video_intelligence USING hnsw (content_embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Remix Studio + synthesis
-- ---------------------------------------------------------------------------
CREATE TABLE brand_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    context TEXT NOT NULL,             -- offer, audience, voice, proof points, banned claims
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE remix_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES competitor_videos(id) ON DELETE CASCADE,
    brand_profile_id UUID REFERENCES brand_profiles(id) ON DELETE SET NULL,
    scripts_json JSONB NOT NULL,
    model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE weekly_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start DATE NOT NULL UNIQUE,
    digest_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Functions
-- ---------------------------------------------------------------------------

-- Recompute a creator's baseline (median views of their last 20 videos), then
-- rescore every one of their videos against it. Returns the new median.
CREATE OR REPLACE FUNCTION recompute_competitor_baseline(
    p_competitor_id UUID,
    p_outlier_threshold NUMERIC DEFAULT 2.5
) RETURNS NUMERIC
LANGUAGE plpgsql AS $$
DECLARE
    v_median NUMERIC;
BEGIN
    SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY views)
      INTO v_median
      FROM (
        SELECT views FROM competitor_videos
         WHERE competitor_id = p_competitor_id
         ORDER BY published_at DESC NULLS LAST
         LIMIT 20
      ) last20;

    UPDATE competitors SET median_views_last_20 = v_median WHERE id = p_competitor_id;

    UPDATE competitor_videos v SET
        outlier_multiplier = CASE WHEN v_median > 0 THEN round(v.views / v_median, 2) END,
        engagement_rate = CASE WHEN v.views > 0 THEN round(
            (v.likes + 2 * v.comments + 3 * v.saves + 4 * v.shares)::NUMERIC / v.views * 100, 2) END,
        is_outlier = COALESCE(v_median > 0 AND v.views / v_median >= p_outlier_threshold, FALSE),
        updated_at = now()
     WHERE v.competitor_id = p_competitor_id;

    RETURN v_median;
END;
$$;

-- Semantic search over video content ("cold email pricing with high saves").
CREATE OR REPLACE FUNCTION match_videos(
    query_embedding vector(1536),
    match_count INT DEFAULT 20,
    min_similarity FLOAT DEFAULT 0.2,
    p_platform TEXT DEFAULT NULL
) RETURNS TABLE (video_id UUID, similarity FLOAT)
LANGUAGE sql STABLE AS $$
    SELECT vi.video_id, 1 - (vi.content_embedding <=> query_embedding) AS similarity
      FROM video_intelligence vi
      JOIN competitor_videos v ON v.id = vi.video_id
     WHERE vi.content_embedding IS NOT NULL
       AND (p_platform IS NULL OR v.platform = p_platform)
       AND 1 - (vi.content_embedding <=> query_embedding) >= min_similarity
     ORDER BY vi.content_embedding <=> query_embedding
     LIMIT match_count;
$$;

-- Nearest hooks to a given video's hook (pattern clustering in the drawer).
CREATE OR REPLACE FUNCTION similar_hooks(p_video_id UUID, match_count INT DEFAULT 6)
RETURNS TABLE (video_id UUID, hook_text TEXT, hook_archetype TEXT, similarity FLOAT)
LANGUAGE sql STABLE AS $$
    SELECT o.video_id, o.hook_text, o.hook_archetype::TEXT,
           1 - (o.hook_embedding <=> s.hook_embedding) AS similarity
      FROM video_intelligence s
      JOIN video_intelligence o ON o.video_id <> s.video_id AND o.hook_embedding IS NOT NULL
     WHERE s.video_id = p_video_id AND s.hook_embedding IS NOT NULL
     ORDER BY o.hook_embedding <=> s.hook_embedding
     LIMIT match_count;
$$;

-- Hook & Pattern Matrix: archetype x platform performance over a window.
CREATE OR REPLACE FUNCTION archetype_matrix(p_since TIMESTAMPTZ DEFAULT now() - interval '7 days')
RETURNS TABLE (
    hook_archetype TEXT, platform TEXT, video_count BIGINT,
    avg_multiplier NUMERIC, median_multiplier NUMERIC, avg_views NUMERIC,
    avg_engagement_rate NUMERIC, outlier_count BIGINT
)
LANGUAGE sql STABLE AS $$
    SELECT vi.hook_archetype::TEXT, v.platform::TEXT, count(*),
           round(avg(v.outlier_multiplier), 2),
           round(percentile_cont(0.5) WITHIN GROUP (ORDER BY v.outlier_multiplier)::NUMERIC, 2),
           round(avg(v.views), 0),
           round(avg(v.engagement_rate), 2),
           count(*) FILTER (WHERE v.is_outlier)
      FROM video_intelligence vi
      JOIN competitor_videos v ON v.id = vi.video_id
     WHERE v.published_at >= p_since AND vi.hook_archetype IS NOT NULL
     GROUP BY vi.hook_archetype, v.platform
     ORDER BY 4 DESC NULLS LAST;
$$;

-- Flat, dashboard-friendly view.
CREATE OR REPLACE VIEW outlier_feed AS
SELECT v.id, v.platform, v.external_video_id, v.video_url, v.media_url, v.thumbnail_url,
       v.caption, v.published_at, v.duration_seconds,
       v.views, v.likes, v.comments, v.shares, v.saves,
       v.outlier_multiplier, v.engagement_rate, v.is_outlier, v.processing_status,
       c.id AS competitor_id, c.handle, c.follower_count, c.median_views_last_20, c.niche_category,
       vi.hook_text, vi.hook_archetype, vi.cta_type, vi.primary_topic_cluster, vi.pacing_wpm
  FROM competitor_videos v
  JOIN competitors c ON c.id = v.competitor_id
  LEFT JOIN video_intelligence vi ON vi.video_id = v.id;

-- Public bucket for extracted keyframes (shown in the Video Breakdown Drawer).
INSERT INTO storage.buckets (id, name, public)
VALUES ('keyframes', 'keyframes', TRUE)
ON CONFLICT (id) DO NOTHING;
