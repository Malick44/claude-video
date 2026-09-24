#!/usr/bin/env python3
"""Resolve narrative SFX anchors against a timed transcript.

The plan supplies *decisions* about where an effect belongs. This script only
turns verified word/segment anchors into absolute seconds, then checks that
every referenced effect asset is present. It never guesses word positions from
phrase-level captions.

    python3 resolve_cues.py --plan cue_plan.json --transcript narration.json \
        --output resolved_cues.json [--duration 30.0]

Relative effect paths in the plan are resolved against the plan's directory.
Segment indexes and word occurrence numbers are zero-based and one-based,
respectively (occurrence=1 selects the first matching quotation).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TIME_RE = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")
TAG_RE = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class TimedText:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Transcript:
    words: list[TimedText]
    segments: list[TimedText]


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _timed_text(item: Any, label: str, *, word: bool = False) -> TimedText:
    if not isinstance(item, dict):
        raise ValueError(f"{label} must be an object")
    start = _number(item.get("start", item.get("start_time")), f"{label}.start")
    end = _number(item.get("end", item.get("end_time")), f"{label}.end")
    if start < 0 or end <= start:
        raise ValueError(f"{label} needs 0 <= start < end")
    text = item.get("word") if word else item.get("text")
    if text is None and word:
        text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{label}.text must be nonempty")
    return TimedText(start, end, text.strip())


def _ordered(items: list[TimedText], label: str) -> list[TimedText]:
    if any(items[i].start < items[i - 1].start for i in range(1, len(items))):
        raise ValueError(f"{label} must be ordered by start time")
    return items


def _parse_json_transcript(path: Path) -> Transcript:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"segments": data}
    if not isinstance(data, dict):
        raise ValueError("transcript JSON must be an object or segment array")

    raw_segments = data.get("segments")
    if raw_segments is None:
        raw_segments = data.get("beats", [])
    if not isinstance(raw_segments, list):
        raise ValueError("transcript segments/beats must be an array")
    raw_words = data.get("words", [])
    if not isinstance(raw_words, list):
        raise ValueError("transcript words must be an array")

    segments = [_timed_text(s, f"segment[{i}]") for i, s in enumerate(raw_segments)]
    words = [_timed_text(w, f"word[{i}]", word=True) for i, w in enumerate(raw_words)]
    # Some aligners include the same word list at both levels. The top-level
    # sequence is authoritative when present; concatenating both duplicates
    # matches and may even make a valid transcript appear out of order.
    use_nested_words = not raw_words
    for i, segment in enumerate(raw_segments):
        nested = segment.get("words", []) if isinstance(segment, dict) else []
        if not isinstance(nested, list):
            raise ValueError(f"segment[{i}].words must be an array")
        if use_nested_words:
            words.extend(
                _timed_text(w, f"segment[{i}].words[{j}]", word=True)
                for j, w in enumerate(nested)
            )
    if not words and not segments:
        raise ValueError("transcript contains no timed words or segments")
    return Transcript(_ordered(words, "words"), _ordered(segments, "segments"))


def _seconds(value: str) -> float:
    match = TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid subtitle timestamp: {value!r}")
    hours, minutes, seconds, milliseconds = match.groups()
    if int(seconds) >= 60 or (hours is not None and int(minutes) >= 60):
        raise ValueError(f"invalid subtitle timestamp: {value!r}")
    return (int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)
            + int(milliseconds.ljust(3, "0")) / 1000)


def _parse_subtitles(path: Path) -> Transcript:
    content = path.read_text(encoding="utf-8-sig")
    segments: list[TimedText] = []
    for block in re.split(r"\n\s*\n", content.replace("\r\n", "\n")):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if index is None:
            continue
        left, right = lines[index].split("-->", 1)
        start = _seconds(left)
        # VTT permits cue settings after the end timestamp.
        end = _seconds(right.strip().split()[0])
        subtitle = " ".join(TAG_RE.sub("", line).strip() for line in lines[index + 1:]).strip()
        if not subtitle:
            continue
        segments.append(_timed_text({"start": start, "end": end, "text": subtitle}, "subtitle cue"))
    if not segments:
        raise ValueError("subtitle file contains no timed cues")
    return Transcript([], _ordered(segments, "subtitle cues"))


def load_transcript(path: Path) -> Transcript:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _parse_json_transcript(path)
    if suffix in {".srt", ".vtt"}:
        return _parse_subtitles(path)
    raise ValueError("transcript must be .json, .srt, or .vtt")


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    # A dash or ellipsis separates spoken words; an apostrophe can remain
    # inside one word ("can't" -> "cant").
    raw = re.findall(r"[^\W_]+(?:['’][^\W_]+)*", normalized, flags=re.UNICODE)
    return ["".join(ch for ch in token if ch.isalnum()) for token in raw]


def _quote_matches(words: list[TimedText], quote: str) -> list[tuple[int, int]]:
    target = _tokens(quote)
    if not target:
        raise ValueError("word anchor quote must contain letters or numbers")
    # Aligned word entries should each contain one spoken token. Matching each
    # entry as a unit avoids invented sub-word times when an entry contains more.
    stream = [_tokens(word.text) for word in words]
    matches = []
    for start in range(len(stream) - len(target) + 1):
        window = stream[start:start + len(target)]
        if all(len(part) == 1 for part in window) and [part[0] for part in window] == target:
            matches.append((start, start + len(target) - 1))
    return matches


def _resolve_anchor(anchor: Any, transcript: Transcript, cue_id: str) -> float:
    if not isinstance(anchor, dict):
        raise ValueError(f"cue {cue_id}: anchor must be an object")
    kind = anchor.get("kind")
    if kind == "absolute":
        return _number(anchor.get("seconds"), f"cue {cue_id} absolute seconds")

    edge = anchor.get("edge")
    if edge not in {"start", "end"}:
        raise ValueError(f"cue {cue_id}: anchor edge must be 'start' or 'end'")
    offset = _number(anchor.get("offset_ms", 0), f"cue {cue_id} offset_ms") / 1000

    if kind == "segment":
        index = anchor.get("index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ValueError(f"cue {cue_id}: segment index must be a zero-based integer")
        if index >= len(transcript.segments):
            raise ValueError(f"cue {cue_id}: segment index {index} is out of range")
        item = transcript.segments[index]
    elif kind == "word":
        if not transcript.words:
            raise ValueError(f"cue {cue_id}: word anchor requires word-level timestamps; phrase captions cannot be interpolated")
        quote = anchor.get("quote")
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError(f"cue {cue_id}: word anchor needs a nonempty quote")
        matches = _quote_matches(transcript.words, quote)
        if not matches:
            raise ValueError(f"cue {cue_id}: quote {quote!r} was not found in timed words")
        occurrence = anchor.get("occurrence")
        if occurrence is None:
            if len(matches) != 1:
                raise ValueError(f"cue {cue_id}: quote {quote!r} is ambiguous ({len(matches)} matches); set one-based occurrence")
            match = matches[0]
        else:
            if isinstance(occurrence, bool) or not isinstance(occurrence, int) or occurrence < 1:
                raise ValueError(f"cue {cue_id}: occurrence must be a one-based integer")
            if occurrence > len(matches):
                raise ValueError(f"cue {cue_id}: occurrence {occurrence} exceeds {len(matches)} matches for {quote!r}")
            match = matches[occurrence - 1]
        item = transcript.words[match[0] if edge == "start" else match[1]]
    else:
        raise ValueError(f"cue {cue_id}: anchor kind must be word, segment, or absolute")
    return (item.start if edge == "start" else item.end) + offset


def resolve_plan(plan: dict[str, Any], transcript: Transcript, plan_dir: Path,
                 *, duration: float | None = None) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise ValueError("plan must be an object with version: 1")
    cues = plan.get("cues")
    if not isinstance(cues, list):
        raise ValueError("plan.cues must be an array")
    if duration is None:
        media = plan.get("media", {})
        if isinstance(media, dict):
            duration = media.get("duration_sec")
    if duration is not None:
        duration = _number(duration, "duration")
        if duration <= 0:
            raise ValueError("duration must be positive")

    resolved = []
    seen_ids: set[str] = set()
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise ValueError(f"cue[{i}] must be an object")
        cue_id = cue.get("id")
        if not isinstance(cue_id, str) or not cue_id.strip() or cue_id in seen_ids:
            raise ValueError(f"cue[{i}] needs a unique nonempty id")
        seen_ids.add(cue_id)
        at = _resolve_anchor(cue.get("anchor"), transcript, cue_id)
        if at < 0 or (duration is not None and at >= duration):
            raise ValueError(f"cue {cue_id}: resolved time {at:.3f}s is outside the media timeline")
        asset = cue.get("asset")
        if not isinstance(asset, str) or not asset.strip():
            raise ValueError(f"cue {cue_id}: asset path is required")
        asset_path = Path(asset).expanduser()
        if not asset_path.is_absolute():
            asset_path = plan_dir / asset_path
        asset_path = asset_path.resolve()
        if not asset_path.is_file():
            raise ValueError(f"cue {cue_id}: effect asset does not exist: {asset_path}")
        gain = _number(cue.get("gain_db", 0), f"cue {cue_id} gain_db")
        fade_in = _number(cue.get("fade_in_ms", 0), f"cue {cue_id} fade_in_ms")
        fade_out = _number(cue.get("fade_out_ms", 0), f"cue {cue_id} fade_out_ms")
        if fade_in < 0 or fade_out < 0:
            raise ValueError(f"cue {cue_id}: fades cannot be negative")
        reason = cue.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"cue {cue_id}: reason must be nonempty")
        tension_before = _number(cue.get("tension_before"), f"cue {cue_id} tension_before")
        tension_after = _number(cue.get("tension_after"), f"cue {cue_id} tension_after")
        if not 0 <= tension_before <= 1 or not 0 <= tension_after <= 1:
            raise ValueError(f"cue {cue_id}: tension_before and tension_after must be in 0–1 range")
        item = {
            "id": cue_id,
            "at": round(at, 6),
            "asset": str(asset_path),
            "gain_db": gain,
            "fade_in_ms": fade_in,
            "fade_out_ms": fade_out,
            "reason": reason.strip(),
            "tension_before": tension_before,
            "tension_after": tension_after,
        }
        if "function" in cue:
            function = cue["function"]
            if not isinstance(function, str) or not function.strip():
                raise ValueError(f"cue {cue_id}: function must be nonempty when provided")
            item["function"] = function.strip()
        resolved.append(item)
    resolved.sort(key=lambda cue: cue["at"])
    result = {"version": 1, "cues": resolved}
    if duration is not None:
        result["duration_seconds"] = duration
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="JSON cue plan")
    parser.add_argument("--transcript", type=Path, required=True, help="Timed JSON, SRT, or VTT")
    parser.add_argument("--output", type=Path, required=True, help="Resolved cue manifest JSON")
    parser.add_argument("--duration", type=float, help="Media duration in seconds (overrides plan.media.duration_sec)")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        transcript = load_transcript(args.transcript)
        result = resolve_plan(plan, transcript, args.plan.resolve().parent, duration=args.duration)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"resolve_cues: {exc}", file=sys.stderr)
        return 1
    print(f"Resolved {len(result['cues'])} cue(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
