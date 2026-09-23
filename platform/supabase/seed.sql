-- Demo data for local development: 3 creators across platforms, 60 videos, one
-- fully analyzed viral outlier (the spec's example breakdown). Embeddings are left
-- NULL, so semantic search / similar hooks light up only after real processing.

INSERT INTO competitors (id, platform, handle, follower_count, niche_category) VALUES
  ('00000000-0000-0000-0000-00000000000a', 'tiktok',    'saasgrowthlab', 3100,    'SaaS Marketing'),
  ('00000000-0000-0000-0000-00000000000b', 'instagram', 'bigagencyhq',   2000000, 'SaaS Marketing'),
  ('00000000-0000-0000-0000-00000000000c', 'youtube',   'coldemailcoach', 85000,  'Outbound Sales')
ON CONFLICT DO NOTHING;

INSERT INTO competitor_videos (id, competitor_id, platform, external_video_id, video_url, caption, published_at,
                               duration_seconds, views, likes, comments, shares, saves, processing_status)
SELECT
  ('00000000-0000-0000-0001-' || lpad(to_hex(row_number() OVER ()), 12, '0'))::uuid,
  c.id, c.platform, c.handle || '-' || g,
  'https://example.com/' || c.handle || '/' || g,
  'Demo video ' || g || ' from @' || c.handle,
  now() - (g * 13 || ' hours')::interval,
  30 + (g % 30),
  base * (0.6 + ((g * 37) % 90) / 100.0) * CASE WHEN g IN (2, 11) THEN 6 WHEN g = 7 THEN 3 ELSE 1 END,
  base * 0.06, base * 0.004, base * 0.006, base * 0.01,
  'skipped'
FROM competitors c
JOIN (VALUES ('saasgrowthlab', 3000), ('bigagencyhq', 400000), ('coldemailcoach', 20000)) b(handle, base) ON b.handle = c.handle
CROSS JOIN generate_series(1, 20) g
ON CONFLICT DO NOTHING;

SELECT recompute_competitor_baseline(id) FROM competitors;

UPDATE competitor_videos SET processing_status = 'done', raw_transcript =
  'Stop writing blog posts if you want clients in 2026. Look at this: three SaaS brands lost over half their Google traffic this year. Instead, publish programmatic micro case studies. Comment SCALE and I''ll send you the swipe file.'
WHERE external_video_id = 'saasgrowthlab-2';

INSERT INTO video_intelligence (video_id, hook_text, visual_hook_description, hook_archetype, retention_trigger, cta_type,
                                loop_mechanic, pacing_wpm, primary_topic_cluster, beats_json, remix_notes, analysis_json, model)
SELECT v.id, a->'hook_analysis'->>'verbal_hook', a->'hook_analysis'->>'visual_hook_description', a->'hook_analysis'->>'hook_archetype',
       a->'hook_analysis'->>'retention_trigger', a->'structural_metrics'->>'cta_type', a->'structural_metrics'->>'loop_mechanic',
       (a->'structural_metrics'->>'pacing_words_per_minute')::numeric, a->>'primary_topic_cluster',
       a->'narrative_beats', a->'takeaways_for_remixing', a, 'seed'
FROM competitor_videos v, (SELECT '{
  "hook_analysis": {
    "verbal_hook": "Stop writing blog posts if you want clients in 2026.",
    "on_screen_text_hook": "BLOGGING IS DEAD",
    "visual_hook_description": "Creator pointing aggressively at a split screen with a declining graph.",
    "hook_archetype": "Negative Contrast / Pattern Interrupt",
    "retention_trigger": "Fear of obsolescence"
  },
  "narrative_beats": [
    {"timestamp_range": "0:00 - 0:04", "beat_type": "Hook", "summary": "Declares traditional blogging dead.", "on_screen_text": "BLOGGING IS DEAD"},
    {"timestamp_range": "0:04 - 0:18", "beat_type": "Agitation & Proof", "summary": "Shows Google search traffic drop across 3 SaaS brands.", "on_screen_text": "-54% organic traffic"},
    {"timestamp_range": "0:18 - 0:42", "beat_type": "Actionable Pivot", "summary": "Explains programmatic micro-case studies as the alternative.", "on_screen_text": ""},
    {"timestamp_range": "0:42 - 0:50", "beat_type": "Call To Action", "summary": "Comment SCALE to get the swipe file.", "on_screen_text": "Comment SCALE"}
  ],
  "structural_metrics": {
    "pacing_words_per_minute": 178,
    "cta_type": "Comment Keyword Lead Magnet",
    "cta_text": "Comment SCALE to get the swipe file",
    "loop_mechanic": "Seamless audio transition into sentence one",
    "pattern_interrupts": ["Punch-in zoom at 0:04", "Graph b-roll swap", "Whoosh SFX on each stat"]
  },
  "primary_topic_cluster": "SaaS Lead Gen",
  "takeaways_for_remixing": [
    "Use a specific cutoff year in the hook.",
    "Open with third-party platform drops, not your own product pitch."
  ]
}'::jsonb AS a) x
WHERE v.external_video_id = 'saasgrowthlab-2'
ON CONFLICT (video_id) DO NOTHING;

INSERT INTO brand_profiles (name, context) VALUES
  ('Acme Outbound', 'B2B outbound agency for seed–Series B SaaS. Offer: done-for-you cold email that books 15+ demos/month. Audience: founders and first sales hires. Voice: blunt, numbers-first, no hype. Proof: 212 clients, 4.1% average reply rate. Lead magnet: "Cold Email Teardown" PDF (comment TEARDOWN). Never promise guaranteed revenue.')
ON CONFLICT DO NOTHING;
