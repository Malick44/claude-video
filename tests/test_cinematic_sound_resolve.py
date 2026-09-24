"""Timestamp resolution checks for the cinematic sound design skill."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" /
          "cinematic-sound-designer" / "scripts" / "resolve_cues.py")
spec = importlib.util.spec_from_file_location("resolve_cues", SCRIPT)
assert spec and spec.loader
resolver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = resolver
spec.loader.exec_module(resolver)


def make_plan(asset: Path, anchor: dict, *, cue_id: str = "reveal") -> dict:
    return {"version": 1, "media": {"duration_sec": 10}, "cues": [{
        "id": cue_id,
        "anchor": anchor,
        "asset": asset.name,
        "gain_db": -18,
        "fade_in_ms": 5,
        "fade_out_ms": 30,
        "reason": "The delayed answer lands here.",
        "tension_before": 0.8,
        "tension_after": 0.2,
    }]}


def test_word_phrase_anchor_uses_actual_word_edges_and_offset(tmp_path: Path):
    asset = tmp_path / "hit.wav"
    asset.write_bytes(b"asset")
    transcript_path = tmp_path / "words.json"
    transcript_path.write_text(json.dumps({"words": [
        {"text": "Then", "start": 1.03, "end": 1.31},
        {"text": "everything", "start": 1.32, "end": 1.90},
        {"text": "changed!", "start": 1.91, "end": 2.40},
    ]}))
    transcript = resolver.load_transcript(transcript_path)
    plan = make_plan(asset, {"kind": "word", "quote": "Everything changed", "edge": "end", "offset_ms": -70})
    result = resolver.resolve_plan(plan, transcript, tmp_path)
    assert result["cues"][0]["at"] == 2.33
    assert result["cues"][0]["asset"] == str(asset.resolve())
    assert result["cues"][0]["gain_db"] == -18


def test_repeated_word_requires_occurrence(tmp_path: Path):
    asset = tmp_path / "pulse.wav"
    asset.write_bytes(b"asset")
    transcript = resolver.Transcript(words=[
        resolver.TimedText(0.1, 0.3, "Wait"),
        resolver.TimedText(1.1, 1.3, "wait!"),
    ], segments=[])
    plan = make_plan(asset, {"kind": "word", "quote": "wait", "edge": "start"})
    with pytest.raises(ValueError, match="ambiguous"):
        resolver.resolve_plan(plan, transcript, tmp_path)
    plan["cues"][0]["anchor"]["occurrence"] = 2
    assert resolver.resolve_plan(plan, transcript, tmp_path)["cues"][0]["at"] == 1.1
    plan["cues"][0]["anchor"]["occurrence"] = 3
    with pytest.raises(ValueError, match="exceeds"):
        resolver.resolve_plan(plan, transcript, tmp_path)


@pytest.mark.parametrize("extension,subtitle", [
    ("srt", "1\n00:00:01,200 --> 00:00:02,500\nWhat happened?\n\n"),
    ("vtt", "WEBVTT\n\n00:01.200 --> 00:02.500 align:start\nWhat happened?\n\n"),
])
def test_phrase_subtitle_only_supports_segment_anchor(tmp_path: Path, extension: str, subtitle: str):
    asset = tmp_path / "riser.wav"
    asset.write_bytes(b"asset")
    path = tmp_path / f"narration.{extension}"
    path.write_text(subtitle)
    transcript = resolver.load_transcript(path)
    assert transcript.words == []
    plan = make_plan(asset, {"kind": "segment", "index": 0, "edge": "end", "offset_ms": -250})
    assert resolver.resolve_plan(plan, transcript, tmp_path)["cues"][0]["at"] == 2.25
    plan["cues"][0]["anchor"] = {"kind": "word", "quote": "happened", "edge": "start"}
    with pytest.raises(ValueError, match="word-level timestamps"):
        resolver.resolve_plan(plan, transcript, tmp_path)


def test_whisper_nested_words_and_repo_beats(tmp_path: Path):
    whisper = tmp_path / "whisper.json"
    whisper.write_text(json.dumps({"segments": [{
        "start": 2, "end": 3.5, "text": "The secret is",
        "words": [
            {"word": "The", "start": 2, "end": 2.2},
            {"word": "secret", "start": 2.21, "end": 2.8},
            {"word": "is", "start": 2.9, "end": 3.2},
        ],
    }]}))
    transcript = resolver.load_transcript(whisper)
    assert [word.text for word in transcript.words] == ["The", "secret", "is"]
    assert transcript.segments[0].end == 3.5

    beats = tmp_path / "beats.json"
    beats.write_text(json.dumps({"beats": [
        {"start_time": 0, "end_time": 3.2, "text": "A hook"},
        {"start_time": 3.2, "end_time": 8.8, "text": "The setup"},
    ]}))
    assert resolver.load_transcript(beats).segments[1].start == 3.2


def test_top_level_words_take_precedence_over_duplicate_nested_words(tmp_path: Path):
    words = [
        {"word": "The", "start": 1.0, "end": 1.2},
        {"word": "reveal", "start": 1.3, "end": 1.7},
    ]
    path = tmp_path / "redundant.json"
    path.write_text(json.dumps({
        "words": words,
        "segments": [{"start": 1.0, "end": 1.7, "text": "The reveal", "words": words}],
    }))
    transcript = resolver.load_transcript(path)
    assert len(transcript.words) == 2
    asset = tmp_path / "hit.wav"
    asset.write_bytes(b"asset")
    plan = make_plan(asset, {"kind": "word", "quote": "reveal", "edge": "start"})
    assert resolver.resolve_plan(plan, transcript, tmp_path)["cues"][0]["at"] == 1.3


def test_rejects_outside_timeline_missing_asset_and_bad_timestamps(tmp_path: Path):
    asset = tmp_path / "boom.wav"
    asset.write_bytes(b"asset")
    transcript = resolver.Transcript(words=[], segments=[])
    plan = make_plan(asset, {"kind": "absolute", "seconds": 10})
    with pytest.raises(ValueError, match="outside the media timeline"):
        resolver.resolve_plan(plan, transcript, tmp_path)
    plan["cues"][0]["anchor"]["seconds"] = 0.1
    asset.unlink()
    with pytest.raises(ValueError, match="does not exist"):
        resolver.resolve_plan(plan, transcript, tmp_path)
    asset.write_bytes(b"asset")
    plan["cues"][0]["fade_in_ms"] = -1
    with pytest.raises(ValueError, match="cannot be negative"):
        resolver.resolve_plan(plan, transcript, tmp_path)
    plan["cues"][0]["fade_in_ms"] = 0
    plan["cues"][0]["tension_before"] = "high"
    with pytest.raises(ValueError, match="tension_before"):
        resolver.resolve_plan(plan, transcript, tmp_path)
    plan["cues"][0]["tension_before"] = 1.1
    with pytest.raises(ValueError, match="0–1 range"):
        resolver.resolve_plan(plan, transcript, tmp_path)


def test_cli_writes_resolved_manifest(tmp_path: Path):
    asset = tmp_path / "soft_hit.wav"
    asset.write_bytes(b"asset")
    transcript = tmp_path / "speech.json"
    transcript.write_text(json.dumps({"words": [{"text": "Now", "start": 0.35, "end": 0.6}]}))
    plan = tmp_path / "plan.json"
    planned = make_plan(asset, {"kind": "word", "quote": "now", "edge": "start"})
    planned["cues"][0]["function"] = "reveal impact"
    plan.write_text(json.dumps(planned))
    output = tmp_path / "render" / "resolved.json"
    assert resolver.main(["--plan", str(plan), "--transcript", str(transcript), "--output", str(output)]) == 0
    written = json.loads(output.read_text())
    assert written["version"] == 1
    assert written["cues"][0]["at"] == 0.35
    assert written["cues"][0]["function"] == "reveal impact"
    assert written["duration_seconds"] == 10

    override = tmp_path / "render" / "override.json"
    assert resolver.main(["--plan", str(plan), "--transcript", str(transcript),
                          "--output", str(override), "--duration", "2.5"]) == 0
    assert json.loads(override.read_text())["duration_seconds"] == 2.5
