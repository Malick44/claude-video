// Per-video enrichment: media -> transcript -> multimodal analysis -> embeddings.
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { db, must } from "../db";
import { embed, toVector } from "../embeddings";
import { analyzeVideo } from "../llm/analyze";
import { downloadVideo } from "../media/download";
import { extractAudio, extractKeyframes, probeDuration, type Keyframe } from "../media/frames";
import { transcribe, type Transcript } from "../media/transcribe";
import { cutsPerMinute, wordsPerMinute } from "../pacing";
import type { VideoIntelligence } from "../schema";

export interface VideoRow {
  id: string;
  platform: string;
  video_url: string;
  media_url: string | null;
  caption: string | null;
  duration_seconds: number | null;
  views: number;
  outlier_multiplier: number | null;
  engagement_rate: number | null;
  competitors: { handle: string };
}

export async function loadVideo(id: string): Promise<VideoRow> {
  return must(
    await db()
      .from("competitor_videos")
      .select("id, platform, video_url, media_url, caption, duration_seconds, views, outlier_multiplier, engagement_rate, competitors(handle)")
      .eq("id", id)
      .single(),
    "load video",
  ) as unknown as VideoRow;
}

export async function setStatus(id: string, status: string, error?: string) {
  must(
    await db().from("competitor_videos").update({ processing_status: status, processing_error: error ?? null }).eq("id", id),
    "set status",
  );
}

/**
 * Download, extract frames + audio, transcribe, analyze. All in one step because
 * the local media files do not survive across worker invocations.
 */
export async function enrichVideo(video: VideoRow): Promise<{ analysis: VideoIntelligence; model: string; transcript: Transcript }> {
  const dir = await mkdtemp(join(tmpdir(), `vid-${video.id}-`));
  try {
    const file = await downloadVideo({ mediaUrl: video.media_url, videoUrl: video.video_url, dir });
    const duration = (await probeDuration(file)) ?? video.duration_seconds;

    const [{ frames, sceneCutTimes }, audio] = await Promise.all([extractKeyframes(file, dir, duration), extractAudio(file, dir)]);
    const transcript: Transcript = audio ? await transcribe(audio) : { text: "", words: [], sentimentSegments: [] };

    const keyframes = await uploadFrames(video.id, frames);
    const wpm = wordsPerMinute(transcript.words);
    const cpm = cutsPerMinute(sceneCutTimes, duration);

    must(
      await db()
        .from("competitor_videos")
        .update({
          raw_transcript: transcript.text,
          transcript_words: transcript.words,
          keyframes: { frames: keyframes, scene_cut_times: sceneCutTimes, cuts_per_minute: cpm },
          duration_seconds: duration,
        })
        .eq("id", video.id),
      "store media",
    );

    // Hook frames first (the spec's "first 3 frames"), then scene cuts for pacing/overlays.
    const { analysis, model } = await analyzeVideo({
      platform: video.platform,
      handle: video.competitors.handle,
      caption: video.caption,
      durationSeconds: duration,
      metrics: { views: video.views, outlierMultiplier: video.outlier_multiplier, engagementRate: video.engagement_rate },
      transcript,
      frames,
      measured: { wpm, cutsPerMinute: cpm, sceneCuts: sceneCutTimes.length },
    });
    return { analysis, model, transcript };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

async function uploadFrames(videoId: string, frames: Keyframe[]) {
  const bucket = db().storage.from("keyframes");
  const out: { t: number; kind: string; url: string }[] = [];
  for (const f of frames) {
    const key = `${videoId}/${f.path.split("/").pop()}`;
    const { error } = await bucket.upload(key, await readFile(f.path), { contentType: "image/jpeg", upsert: true });
    if (error) {
      // Frames are only for display; analysis reads them from local disk, so don't fail the video.
      console.warn(`keyframe upload skipped (${error.message})`);
      return [];
    }
    out.push({ t: f.t, kind: f.kind, url: bucket.getPublicUrl(key).data.publicUrl });
  }
  return out;
}

export async function storeIntelligence(videoId: string, analysis: VideoIntelligence, model: string, transcriptText: string) {
  const hook = [analysis.hook_analysis.verbal_hook, analysis.hook_analysis.on_screen_text_hook].filter(Boolean).join(" | ");
  const contentDoc = [
    `Hook: ${hook}`,
    `Archetype: ${analysis.hook_analysis.hook_archetype}`,
    `Topic: ${analysis.primary_topic_cluster}`,
    `CTA: ${analysis.structural_metrics.cta_type} — ${analysis.structural_metrics.cta_text}`,
    `Beats: ${analysis.narrative_beats.map((b) => `${b.beat_type}: ${b.summary}`).join(" / ")}`,
    `Transcript: ${transcriptText.slice(0, 6000)}`,
  ].join("\n");
  const [hookEmb, contentEmb] = await embed([hook || analysis.hook_analysis.visual_hook_description, contentDoc]);

  must(
    await db()
      .from("video_intelligence")
      .upsert(
        {
          video_id: videoId,
          hook_text: hook,
          visual_hook_description: analysis.hook_analysis.visual_hook_description,
          hook_archetype: analysis.hook_analysis.hook_archetype,
          retention_trigger: analysis.hook_analysis.retention_trigger,
          cta_type: analysis.structural_metrics.cta_type,
          loop_mechanic: analysis.structural_metrics.loop_mechanic,
          pacing_wpm: analysis.structural_metrics.pacing_words_per_minute,
          primary_topic_cluster: analysis.primary_topic_cluster,
          beats_json: analysis.narrative_beats,
          remix_notes: analysis.takeaways_for_remixing,
          analysis_json: analysis,
          model,
          hook_embedding: toVector(hookEmb),
          content_embedding: toVector(contentEmb),
        },
        { onConflict: "video_id" },
      ),
    "store intelligence",
  );
}
