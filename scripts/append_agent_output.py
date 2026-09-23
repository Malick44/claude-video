#!/usr/bin/env python3
"""
append_agent_output.py
Unified CSV output logger and tracking system for claude-video agent pipelines.

Enables agents (dylan_hook_voiceover, auk_voiceover, character_design,
seedance_video_deconstructor, capcut_video_assembler, etc.) to append or upsert
structured run outputs to a central CSV file.

Supports:
1. Direct CLI manual entry
2. Automatic parsing from an agent's output folder (reading transcript.json, clean_voiceover.txt, etc.)
3. Recursive scanning of a project directory (e.g. outputs/voicereader_ugc_scripts)
4. Python module import (append_agent_output, upsert_agent_output)
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Canonical CSV column schema
CSV_COLUMNS = [
    "id",
    "timestamp",
    "agent",
    "project",
    "title",
    "angle",
    "hook_headline",
    "duration_sec",
    "word_count",
    "wpm",
    "target_audience",
    "clean_voiceover",
    "audio_path",
    "visual_prompt",
    "status",
    "output_dir",
    "notes",
]


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """Finds the root of the claude-video workspace."""
    cur = (start_path or Path(__file__)).resolve()
    for parent in [cur] + list(cur.parents):
        if (parent / ".git").exists() or (parent / "skills").is_dir():
            return parent
    return Path.cwd().resolve()


def get_default_csv_path() -> Path:
    """Returns the canonical path for the central agent output CSV."""
    repo_root = find_repo_root()
    outputs_dir = repo_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir / "agent_outputs.csv"


def init_csv_if_missing(csv_path: Path) -> None:
    """Initializes the CSV with headers if it does not exist or is empty."""
    csv_path = Path(csv_path).resolve()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)


def read_existing_rows(csv_path: Path) -> List[Dict[str, str]]:
    """Reads all rows from CSV into list of dicts."""
    csv_path = Path(csv_path).resolve()
    if not csv_path.exists():
        return []
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_all_rows(rows: List[Dict[str, str]], csv_path: Path) -> None:
    """Overwrites CSV with given rows using standard schema."""
    csv_path = Path(csv_path).resolve()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            clean_row = {col: str(r.get(col, "") or "") for col in CSV_COLUMNS}
            writer.writerow(clean_row)


def normalize_entry(entry: Dict[str, Any]) -> Dict[str, str]:
    """Ensures all columns are present with string values and default timestamp."""
    row = {col: "" for col in CSV_COLUMNS}
    for k, v in entry.items():
        if k in row and v is not None:
            row[k] = str(v).strip()

    if not row["timestamp"]:
        row["timestamp"] = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")

    return row


def upsert_agent_output(
    entry: Dict[str, Any],
    csv_path: Optional[Path] = None,
    match_key: str = "id",
) -> None:
    """
    Appends or updates an agent output entry in the CSV file.
    If match_key exists and is non-empty, updates the matching row; otherwise appends.
    """
    path = Path(csv_path or get_default_csv_path()).resolve()
    init_csv_if_missing(path)

    new_row = normalize_entry(entry)
    target_id = new_row.get(match_key, "").strip()

    rows = read_existing_rows(path)
    updated = False

    if target_id:
        for idx, r in enumerate(rows):
            if r.get(match_key, "").strip() == target_id:
                # Merge: only override with non-empty values from new_row
                for col in CSV_COLUMNS:
                    new_val = new_row.get(col, "").strip()
                    if new_val:
                        rows[idx][col] = new_val
                updated = True
                break

    if not updated:
        rows.append(new_row)

    write_all_rows(rows, path)


def append_agent_output(
    entry: Dict[str, Any],
    csv_path: Optional[Path] = None,
) -> None:
    """Appends a new row unconditionally to the CSV file."""
    path = Path(csv_path or get_default_csv_path()).resolve()
    init_csv_if_missing(path)
    new_row = normalize_entry(entry)

    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writerow(new_row)


def parse_agent_output_dir(dir_path: Path, default_project: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Parses an agent output directory and extracts structured fields.
    Checks for transcript.json, clean_voiceover.txt, audio files, and scripts.
    """
    d = Path(dir_path).resolve()
    if not d.is_dir():
        return None

    entry: Dict[str, Any] = {
        "output_dir": str(d),
        "status": "script_ready",
        "agent": "dylan_hook_voiceover",
        "project": default_project or d.parent.name,
    }

    transcript_json = d / "transcript.json"
    clean_txt = d / "clean_voiceover.txt"

    # Check for audio files (.wav or .mp3)
    audio_files = list(d.glob("*.wav")) + list(d.glob("*.mp3"))
    if audio_files:
        entry["audio_path"] = str(audio_files[0])
        entry["status"] = "audio_ready"

    if transcript_json.exists():
        try:
            with open(transcript_json, encoding="utf-8") as f:
                data = json.load(f)
            entry["id"] = data.get("id") or d.name
            entry["title"] = data.get("title", "")
            entry["angle"] = data.get("angle", "")
            entry["target_audience"] = data.get("target_audience", "")
            entry["duration_sec"] = data.get("target_duration_sec", "")
            entry["word_count"] = data.get("total_words", "")
            entry["wpm"] = data.get("cadence_wpm", "")

            beats = data.get("beats", [])
            if beats and isinstance(beats, list):
                hook_beat = beats[0]
                entry["hook_headline"] = hook_beat.get("banner_headline", "")
                
                # Combine visual actions
                visual_actions = [
                    f"[{b.get('name', 'Beat')}]: {b.get('visual_action', '')}"
                    for b in beats
                    if b.get("visual_action")
                ]
                if visual_actions:
                    entry["visual_prompt"] = " | ".join(visual_actions)
        except Exception as e:
            print(f"[!] Warning reading {transcript_json}: {e}", file=sys.stderr)

    if not entry.get("id"):
        entry["id"] = d.name

    if clean_txt.exists():
        entry["clean_voiceover"] = clean_txt.read_text(encoding="utf-8").strip()

    return entry


def scan_and_sync_directory(
    parent_dir: Path,
    csv_path: Optional[Path] = None,
    default_project: Optional[str] = None,
) -> int:
    """
    Scans child directories under parent_dir and upserts all parsed entries into the CSV.
    """
    parent = Path(parent_dir).resolve()
    if not parent.is_dir():
        print(f"[!] Directory not found: {parent}", file=sys.stderr)
        return 0

    count = 0
    subdirs = sorted([p for p in parent.iterdir() if p.is_dir()])
    for sub in subdirs:
        parsed = parse_agent_output_dir(sub, default_project=default_project or parent.name)
        if parsed and (parsed.get("clean_voiceover") or parsed.get("title")):
            upsert_agent_output(parsed, csv_path=csv_path)
            count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified CSV output logger and tracking tool for claude-video agent pipelines."
    )
    parser.add_argument("--csv", type=str, default=None, help="Path to destination CSV (default: outputs/agent_outputs.csv)")
    parser.add_argument("--scan-dir", type=str, default=None, help="Scan parent folder and upsert all agent subfolder outputs")
    parser.add_argument("--from-dir", type=str, default=None, help="Parse single agent output folder and upsert")
    parser.add_argument("--id", type=str, default=None, help="Unique item ID")
    parser.add_argument("--agent", type=str, default="agent", help="Name of agent (e.g. dylan_hook_voiceover, auk_voiceover)")
    parser.add_argument("--project", type=str, default="", help="Project or campaign name")
    parser.add_argument("--title", type=str, default="", help="Title / Topic")
    parser.add_argument("--angle", type=str, default="", help="Strategic angle / hook category")
    parser.add_argument("--hook-headline", type=str, default="", help="Banner headline / scroll-stop hook")
    parser.add_argument("--duration", type=str, default="", help="Duration in seconds")
    parser.add_argument("--words", type=str, default="", help="Word count")
    parser.add_argument("--wpm", type=str, default="", help="Cadence WPM")
    parser.add_argument("--target-audience", type=str, default="", help="Target audience")
    parser.add_argument("--voiceover", type=str, default="", help="Clean spoken voiceover text")
    parser.add_argument("--audio-path", type=str, default="", help="Path to generated audio file (.wav/.mp3)")
    parser.add_argument("--visual-prompt", type=str, default="", help="Visual action prompt or Seedance direction")
    parser.add_argument("--status", type=str, default="script_ready", help="Status (script_ready, audio_ready, video_ready, assembled, published)")
    parser.add_argument("--output-dir", type=str, default="", help="Output folder containing assets")
    parser.add_argument("--notes", type=str, default="", help="Optional notes or tags")
    parser.add_argument("--no-upsert", action="store_true", help="Always append new row without checking existing ID")

    args = parser.parse_args()
    csv_file = Path(args.csv).resolve() if args.csv else get_default_csv_path()

    init_csv_if_missing(csv_file)

    if args.scan_dir:
        scanned = scan_and_sync_directory(Path(args.scan_dir), csv_path=csv_file)
        print(f"[+] Scanned and synced {scanned} items from {args.scan_dir} into {csv_file}")
        return

    if args.from_dir:
        parsed = parse_agent_output_dir(Path(args.from_dir))
        if parsed:
            upsert_agent_output(parsed, csv_path=csv_file)
            print(f"[+] Synced {parsed.get('id')} from {args.from_dir} into {csv_file}")
        else:
            print(f"[!] Could not parse output directory: {args.from_dir}", file=sys.stderr)
        return

    # Direct manual entry
    if args.id or args.title or args.voiceover:
        entry = {
            "id": args.id or f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "agent": args.agent,
            "project": args.project,
            "title": args.title,
            "angle": args.angle,
            "hook_headline": args.hook_headline,
            "duration_sec": args.duration,
            "word_count": args.words,
            "wpm": args.wpm,
            "target_audience": args.target_audience,
            "clean_voiceover": args.voiceover,
            "audio_path": args.audio_path,
            "visual_prompt": args.visual_prompt,
            "status": args.status,
            "output_dir": args.output_dir,
            "notes": args.notes,
        }
        if args.no_upsert:
            append_agent_output(entry, csv_path=csv_file)
            print(f"[+] Appended new row for {entry['id']} to {csv_file}")
        else:
            upsert_agent_output(entry, csv_path=csv_file)
            print(f"[+] Upserted row for {entry['id']} into {csv_file}")
    else:
        print(f"[i] CSV is initialized and ready at: {csv_file}")
        print("Use --scan-dir, --from-dir, or specify fields (--id, --title, --voiceover) to append output.")


if __name__ == "__main__":
    main()
