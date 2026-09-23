#!/usr/bin/env python3
"""Stage assets and optionally render a preview for the legacy top/down recipe."""

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Resolve template script location relative to skill root
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_SCRIPT = SCRIPT_DIR / "top_down_split_template.py"


def format_srt_timestamp(seconds: float) -> str:
    """Formats float seconds into SRT timestamp format: HH:MM:SS,mmm"""
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("SRT timestamps must be finite, nonnegative seconds")
    total_millis = round(seconds * 1000)
    total_seconds, millis = divmod(total_millis, 1000)
    hrs, remainder = divmod(total_seconds, 3600)
    mins, secs = divmod(remainder, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_srt(beats: list, output_srt_path: Path):
    """Generates standard .srt subtitle file from beat entries."""
    lines = []
    for i, b in enumerate(beats, start=1):
        start = float(b["start"])
        end = float(b["end"])
        if end <= start:
            raise ValueError(f"Caption {i} must end after it starts")
        start_str = format_srt_timestamp(start)
        end_str = format_srt_timestamp(end)
        text = str(b["text"]).strip()
        if not text:
            raise ValueError(f"Caption {i} has no text")
        lines.append(f"{i}")
        lines.append(f"{start_str} --> {end_str}")
        lines.append(text)
        lines.append("")

    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Created CapCut subtitle file: {output_srt_path.name}")


def probe_duration(path: Path) -> float:
    """Read a media file's duration in seconds."""
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ], text=True).strip()
    duration = float(result)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"Media has no positive duration: {path}")
    return duration


def find_local_capcut_project(project_identifier: Optional[str] = None) -> Optional[Path]:
    """Find an explicitly named local draft for read-only inspection."""
    if not project_identifier:
        return None
    if "://" in project_identifier:
        raise ValueError("A CapCut share URL does not identify a local draft; use its local name or path")

    p = Path(project_identifier).expanduser()
    if p.is_dir():
        return p

    clean_name = project_identifier.strip()

    capcut_draft_dir = Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
    root_meta_path = capcut_draft_dir / "root_meta_info.json"

    if root_meta_path.exists():
        try:
            with open(root_meta_path) as f:
                data = json.load(f)
            drafts = data.get("all_draft_store", [])
            for d in drafts:
                if d.get("draft_name") == clean_name and d.get("draft_fold_path"):
                    fold = Path(d["draft_fold_path"])
                    if fold.is_dir():
                        return fold
        except Exception as e:
            print(f"[!] Warning checking root_meta_info: {e}")

    # Fallback to direct check
    if (capcut_draft_dir / clean_name).is_dir():
        return capcut_draft_dir / clean_name

    return None


def inspect_capcut_project_template(project_dir: Path) -> dict:
    """Extracts template and layout information from local CapCut project files."""
    info = {"project_dir": str(project_dir), "template_name": "Standard 9:16"}
    if not project_dir or not project_dir.exists():
        return info

    patch_draft = None
    for p in project_dir.glob("Timelines/*/attachment/patch/mini_draft.json"):
        patch_draft = p
        break

    if patch_draft and patch_draft.exists():
        try:
            with open(patch_draft) as f:
                d = json.load(f).get("mini_draft_data", {})
            mds = d.get("material_drafts", [])
            if mds:
                seg_map = {s["id"]: s for s in mds[0].get("segments", [])}
                tracks = mds[0].get("draft", {}).get("tracks", [])
                info["tracks_count"] = len(tracks)
                info["segments"] = []
                for t in tracks:
                    for seg_id in t.get("segments", []):
                        if seg_id in seg_map:
                            s = seg_map[seg_id]
                            info["segments"].append({
                                "material_name": s.get("material", {}).get("material_name"),
                                "transform": s.get("clip", {}).get("transform"),
                                "scale": s.get("clip", {}).get("scale")
                            })
            if d.get("segments"):
                info["template_name"] = d["segments"][0].get("material", {}).get("material_name", "Split Screen")
        except Exception as e:
            print(f"[!] Note on reading template patch: {e}")

    return info


def create_capcut_package(
    top_video: Path,
    bottom_video: Path,
    audio_path: Path,
    output_dir: Path,
    beats: list = None,
    render_master: bool = False,
    capcut_project: str = None,
    manifest_path: Optional[Path] = None,
) -> Path:
    """Create a split-video asset package without modifying a CapCut draft."""
    target_project_dir = find_local_capcut_project(capcut_project)
    if capcut_project and target_project_dir is None:
        raise FileNotFoundError(f"Local CapCut project not found: {capcut_project}")

    aud_dur = probe_duration(audio_path)
    top_dur = probe_duration(top_video)
    if top_dur < aud_dur - 0.001:
        raise ValueError(
            f"Top story video is shorter than audio ({top_dur:.3f}s < {aud_dur:.3f}s); "
            "supply enough story footage or trim the audio"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Assembling CapCut project package in: {output_dir}")

    if target_project_dir:
        print(f"[+] Read-only inspection of CapCut project: {target_project_dir.name} ({target_project_dir})")
        template_info = inspect_capcut_project_template(target_project_dir)
        print(f"    - Active Template: {template_info.get('template_name')}")

    track1_top = output_dir / "track1_top_story.mp4"
    track2_bottom = output_dir / "track2_bottom_presenter.mp4"
    track3_audio = output_dir / f"track3_voiceover{audio_path.suffix}"
    srt_file = output_dir / "captions.srt"
    master_preview = output_dir / "master_preview_9x16.mp4"
    launcher_sh = output_dir / "open_in_capcut.sh"
    readme_md = output_dir / "CAPCUT_QUICK_START.md"

    # 1. Stage Top Story Track (ensure 1080x960, no audio)
    print("    [1/5] Staging Track 1 (Top Story Video)...")
    cmd_top = [
        "ffmpeg", "-y",
        "-i", str(top_video),
        "-t", f"{aud_dur:.3f}",
        "-vf", "scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        str(track1_top)
    ]
    subprocess.run(cmd_top, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 2. Stage Bottom Presenter Track (ensure 1080x960, looped to voiceover length, no audio)
    print("    [2/5] Staging Track 2 (Bottom Presenter Video)...")
    cmd_bot = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(bottom_video),
        "-t", f"{aud_dur:.3f}",
        "-vf", "scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        str(track2_bottom)
    ]
    subprocess.run(cmd_bot, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 3. Stage Audio Track
    print("    [3/5] Staging supplied audio...")
    shutil.copy2(audio_path, track3_audio)

    # 4. Generate subtitles only when the user supplied timed text.
    if beats:
        print("    [4/5] Generating Subtitles (captions.srt)...")
        generate_srt(beats, srt_file)
    else:
        srt_file.unlink(missing_ok=True)

    preview_manifest = output_dir / "preview_manifest.json"
    if beats and manifest_path is None:
        preview_manifest.write_text(json.dumps({"captions": beats}), encoding="utf-8")
        manifest_path = preview_manifest
    elif manifest_path is None or manifest_path.resolve() != preview_manifest.resolve():
        preview_manifest.unlink(missing_ok=True)

    # 5. Create macOS Launcher Script
    launcher_content = f"""#!/bin/bash
# open_in_capcut.sh - Opens CapCut Desktop and reveals assets
DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
echo "[*] Revealing CapCut assets in Finder..."
open "$DIR"

if [ -d "/Applications/CapCut.app" ]; then
    echo "[*] Launching CapCut Desktop..."
    open -a "/Applications/CapCut.app"
else
    echo "[!] CapCut.app not found in /Applications. Please open CapCut manually."
fi
"""
    with open(launcher_sh, "w") as f:
        f.write(launcher_content)
    launcher_sh.chmod(0o755)

    # 6. Create CapCut Quick Start Guide
    caption_asset_line = "- `captions.srt` — Timed subtitles to import into CapCut.\n" if beats else ""
    preview_asset_line = "- `master_preview_9x16.mp4` — Pre-rendered vertical split preview.\n" if render_master else ""
    caption_step = (
        "5. In CapCut, import `captions.srt` using the local captions import controls."
        if beats else "5. Add captions in CapCut if this edit needs them."
    )
    readme_content = f"""# CapCut Desktop Assembly Guide

This package contains separated tracks for a top/down vertical video. Import them into CapCut to edit the timeline.

## Target CapCut Project: {target_project_dir.name if target_project_dir else 'Choose a project in CapCut'}
- Staging Directory: `{output_dir}`
- Project Folder: `{target_project_dir if target_project_dir else 'Not selected'}`

## Staged Assets
- `track1_top_story.mp4` — 1080x960 incident/story video (Top Half).
- `track2_bottom_presenter.mp4` — 1080x960 animated presenter headshot (Bottom Half).
- `{track3_audio.name}` — Supplied audio in its original format.
{caption_asset_line}{preview_asset_line}

## CapCut Import Workflow
1. Run `./open_in_capcut.sh` to launch CapCut Desktop and reveal files.
2. In CapCut, open **{target_project_dir.name if target_project_dir else 'a new or existing 9:16 project'}**.
3. Import `track1_top_story.mp4` and `track2_bottom_presenter.mp4`:
   - Place `track1_top_story.mp4` in the upper half.
   - Place `track2_bottom_presenter.mp4` in the lower half and check the preview.
4. Drag `{track3_audio.name}` onto an audio track.
{caption_step}
"""
    with open(readme_md, "w") as f:
        f.write(readme_content)

    # 7. Render Master Preview if requested
    if render_master:
        if not TEMPLATE_SCRIPT.exists():
            raise FileNotFoundError(f"Split preview script not found: {TEMPLATE_SCRIPT}")
        print("    [5/5] Rendering Master Top/Down 9:16 Video Preview...")
        cmd_master = [
            sys.executable, str(TEMPLATE_SCRIPT),
            "--top-video", str(track1_top),
            "--bottom-video", str(track2_bottom),
            "--audio", str(track3_audio),
            "--output", str(master_preview)
        ]
        if manifest_path is not None:
            cmd_master.extend(["--manifest", str(manifest_path)])
        subprocess.run(cmd_master, check=True)
        print(f"[+] Master video rendered at: {master_preview}")
    else:
        master_preview.unlink(missing_ok=True)

    print(f"\n[✓] CapCut project bundle successfully assembled at: {output_dir}")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Assemble CapCut Desktop staging package.")
    parser.add_argument("--top-video", required=True, help="Path to top story video")
    parser.add_argument("--bottom-video", required=True, help="Path to bottom presenter video")
    parser.add_argument("--audio", required=True, help="Path to voiceover audio track")
    parser.add_argument("--output-dir", default="work/capcut_package", help="Output package directory")
    parser.add_argument("--transcript-json", help="Optional path to transcript or beat JSON")
    parser.add_argument("--render-master", action=argparse.BooleanOptionalAction, default=False, help="Render master preview")
    parser.add_argument("--capcut-project", help="Exact name or path of local CapCut project for read-only inspection")

    args = parser.parse_args()

    beats = None
    manifest_path = Path(args.transcript_json) if args.transcript_json else None
    if manifest_path is not None:
        if not manifest_path.is_file():
            parser.error(f"Transcript/manifest file not found: {manifest_path}")
        with open(manifest_path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            parser.error("Transcript/manifest JSON must be an object")
        beats = data.get("captions", data.get("beats"))

    create_capcut_package(
        top_video=Path(args.top_video),
        bottom_video=Path(args.bottom_video),
        audio_path=Path(args.audio),
        output_dir=Path(args.output_dir),
        beats=beats,
        render_master=args.render_master,
        capcut_project=args.capcut_project,
        manifest_path=manifest_path,
    )


if __name__ == "__main__":
    main()
