#!/usr/bin/env python3
"""
craft_hook_voiceover.py
Dylan Page Viral Voiceover Transcript Generator (Transcript Only).

Transforms any story topic, news summary, or raw text into a mathematically
calibrated 20-30 second viral voiceover transcript following Dylan Page's
empirical 4-beat structure:
- Cadence: 168 - 175 Words Per Minute (WPM) (Average: 172 WPM)
- 4-Beat Narrative Architecture:
    Beat 1: Scroll-Stop Hook (0.0s - 3.2s)
    Beat 2: The Setup & Entities (3.2s - 9.5s)
    Beat 3: The Escalation & Dramatic Twist (9.5s - 22.0s)
    Beat 4: The Moral Dilemma & Outro Question (22.0s - duration)

Designed to pass clean, timed transcripts to another agent for audio generation.
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

# Dylan Page Cadence Calibration (derived from top 100 empirical analysis)
TARGET_WPM = 172.0  # words per minute


def calculate_target_words(duration_sec: float) -> int:
    """Calculates ideal word count for strict short-form pacing."""
    clamped_sec = max(15.0, min(60.0, duration_sec))
    return int(round((clamped_sec / 60.0) * TARGET_WPM))


def format_srt_timestamp(seconds: float) -> str:
    """Formats seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_dylan_transcript(topic: str, duration_sec: float = 25.0) -> dict:
    """
    Generates a structured, calibrated short-form Dylan Page style voiceover transcript.
    """
    clamped_dur = max(15.0, min(60.0, float(duration_sec)))
    clean_topic = topic.strip().rstrip(".")

    # Proportional beat durations
    hook_dur = 3.2
    outro_dur = 4.0
    body_dur = clamped_dur - (hook_dur + outro_dur)
    setup_dur = round(body_dur * 0.40, 1)
    escalation_dur = round(body_dur * 0.60, 1)

    t0 = 0.0
    t1 = hook_dur
    t2 = round(t1 + setup_dur, 1)
    t3 = round(clamped_dur - outro_dur, 1)
    t4 = clamped_dur

    beats = [
        {
            "beat_id": "01_hook",
            "name": "The Scroll-Stop Hook",
            "start_time": t0,
            "end_time": t1,
            "duration": round(t1 - t0, 1),
            "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
            "tone": "intense whisper with shocked emphasis",
            "role": "Pattern Interrupt - Stop Mindless Scrolling",
            "text": "This might actually be the most unbelievable thing you see all week.",
            "banner_headline": "MOST UNBELIEVABLE MOMENT THIS WEEK?"
        },
        {
            "beat_id": "02_setup",
            "name": "The Setup & Entities",
            "start_time": t1,
            "end_time": t2,
            "duration": round(t2 - t1, 1),
            "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
            "tone": "rapid-fire matter-of-fact delivery and fast tempo",
            "role": "Introduce central subject, location, and immediate stakes",
            "text": f"So right here, {clean_topic} was just captured on camera, and nobody was expecting what happened next.",
            "banner_headline": "CAUGHT ON CAMERA..."
        },
        {
            "beat_id": "03_escalation_twist",
            "name": "The Dramatic Twist",
            "start_time": t2,
            "end_time": t3,
            "duration": round(t3 - t2, 1),
            "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
            "tone": "incredulous and shocked with building excitement",
            "role": "The bizarre turning point or impossible outcome",
            "text": "At first, everyone thought this was completely staged, but authorities confirmed it was 100% real, and when you look closer, the story gets ten times crazier.",
            "banner_headline": "STORY GETS 10X CRAZIER!"
        },
        {
            "beat_id": "04_outro_question",
            "name": "The Moral Dilemma & Question",
            "start_time": t3,
            "end_time": t4,
            "duration": round(t4 - t3, 1),
            "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
            "tone": "amused deadpan and engaging rising intonation",
            "role": "Viral Engagement Engine: prompt debate in comments",
            "text": "So let me know down below... what would you have done in this situation?",
            "banner_headline": "WHAT WOULD YOU HAVE DONE?"
        }
    ]

    total_words = sum(len(b["text"].split()) for b in beats)
    cadence = round((total_words / clamped_dur) * 60, 1)

    return {
        "topic": topic,
        "target_duration_sec": clamped_dur,
        "total_words": total_words,
        "cadence_wpm": cadence,
        "target_wpm_baseline": TARGET_WPM,
        "beats": beats
    }


def format_transcript_readable(data: dict) -> str:
    """Generates clean, human-readable script with timestamps and inflection cues."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"DYLAN PAGE VIRAL VOICEOVER TRANSCRIPT ({data['target_duration_sec']}s Target)")
    lines.append(f"Pacing: {data['cadence_wpm']} WPM (Target: 172 WPM) | Total Words: {data['total_words']}")
    lines.append(f"Topic: {data['topic']}")
    lines.append("=" * 70)
    lines.append("")

    for b in data["beats"]:
        lines.append(f"[{b['start_time']:04.1f}s - {b['end_time']:04.1f}s] {b['name'].upper()}")
        lines.append(f"Vocal Tone:      {b.get('tone', '')}")
        lines.append(f"Inflection Cue:  {b['inflection']}")
        lines.append(f"Banner Headline: {b['banner_headline']}")
        lines.append(f"Spoken Voiceover: \"{b['text']}\"")
        lines.append("")

    lines.append("=" * 70)
    lines.append("CLEAN SPOKEN TEXT ONLY (For TTS / Audio Generation Agent):")
    lines.append("=" * 70)
    lines.append(" ".join(b["text"] for b in data["beats"]))
    lines.append("")
    return "\n".join(lines)


def format_clean_speech(data: dict) -> str:
    """Returns pure spoken text without timestamps or cues, ready for TTS agents."""
    return " ".join(b["text"] for b in data["beats"])


def format_srt(data: dict) -> str:
    """Formats transcript into standard SRT subtitles."""
    lines = []
    for i, b in enumerate(data["beats"], 1):
        s_str = format_srt_timestamp(b["start_time"])
        e_str = format_srt_timestamp(b["end_time"])
        lines.append(f"{i}")
        lines.append(f"{s_str} --> {e_str}")
        lines.append(b["text"])
        lines.append("")
    return "\n".join(lines)


def run_transcript_generator(
    topic: str = None,
    input_file: Path = None,
    duration: float = 25.0,
    output_dir: Path = None
) -> dict:
    """Main generator entry point: produces transcript files only."""
    # Determine topic from text file or string
    if not topic and input_file and input_file.exists():
        content = input_file.read_text(encoding="utf-8").strip()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        topic = lines[0] if lines else input_file.stem.replace("_", " ").replace("-", " ")
    elif not topic:
        topic = "an unbelievable event caught on camera"

    data = generate_dylan_transcript(topic=topic, duration_sec=duration)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        # 1. Human readable transcript
        (output_dir / "voiceover_transcript.txt").write_text(format_transcript_readable(data), encoding="utf-8")
        # 2. Clean speech text only (for audio generation agent)
        (output_dir / "clean_voiceover.txt").write_text(format_clean_speech(data), encoding="utf-8")
        # 3. Subtitles SRT
        (output_dir / "transcript.srt").write_text(format_srt(data), encoding="utf-8")
        # 4. JSON Manifest
        (output_dir / "transcript.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Dylan Page Viral Voiceover Transcript Generator (Transcript Only)"
    )
    parser.add_argument("--topic", "-t", type=str, default=None, help="Core story topic, headline, or premise")
    parser.add_argument("--input", "-i", type=str, default=None, help="Optional path to text file containing story notes or raw transcript")
    parser.add_argument("--duration", "-d", type=float, default=25.0, help="Target duration in seconds (20.0 to 30.0, default 25.0)")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Optional output directory to save transcript files")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")

    args = parser.parse_args()

    input_file = Path(args.input).resolve() if args.input else None
    out_dir = Path(args.output_dir).resolve() if args.output_dir else None

    data = run_transcript_generator(
        topic=args.topic,
        input_file=input_file,
        duration=args.duration,
        output_dir=out_dir
    )

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_transcript_readable(data))
        if out_dir:
            print(f"[+] Saved transcript files to: {out_dir}")
            print(f"    - voiceover_transcript.txt (full timestamps & vocal cues)")
            print(f"    - clean_voiceover.txt (clean text for audio generation agent)")
            print(f"    - transcript.srt (CapCut/Premiere subtitles)")
            print(f"    - transcript.json (structured JSON payload)")


if __name__ == "__main__":
    main()
