#!/usr/bin/env python3
"""
top_down_split_template.py
A template engine for creating 9:16 vertical top/down split videos:
- Top Half (1080x960): Background story / event / B-roll footage.
- Center Divider: Stylized divider bar with high-contrast borders and kinetic hook headlines.
- Bottom Half (1080x960): Presenter / character reaction clip (looped seamlessly).
- Overlay: Optional user-supplied banners and captions.
- Audio: Supplied audio track.
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path


DEFAULT_FONT = "/System/Library/Fonts/Supplemental/Impact.ttf"
if not Path(DEFAULT_FONT).exists():
    DEFAULT_FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
if not Path(DEFAULT_FONT).exists():
    DEFAULT_FONT = "/System/Library/Fonts/Helvetica.ttc"


def probe_duration(path: Path) -> float:
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


def render_top_down_split(
    top_video: Path,
    bottom_video: Path,
    audio_path: Path,
    output_path: Path,
    banners: list = None,
    captions: list = None,
    divider_height: int = 70,
    divider_color: str = "black@0.95",
    border_color: str = "#FFE600",
    border_width: int = 4,
    font_path: str = DEFAULT_FONT
) -> bool:
    """
    Renders a 1080x1920 Top/Down split video using ffmpeg.
    """
    audio_duration = probe_duration(audio_path)
    top_duration = probe_duration(top_video)
    if top_duration < audio_duration - 0.001:
        print(
            f"[!] Top story video is shorter than audio ({top_duration:.3f}s < "
            f"{audio_duration:.3f}s); supply enough story footage or trim the audio"
        )
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Top half: 1080x960
    # Bottom half: 1080x960
    # Center divider bar: centered around y = 960 (from y=960 - divider_height//2 to y=960 + divider_height//2)
    div_y1 = 960 - (divider_height // 2)
    div_y2 = 960 + (divider_height // 2)

    # ffmpeg filter graph
    # 1. Scale and crop top video to 1080x960
    # 2. Scale and crop bottom video to 1080x960
    # 3. Stack them vertically: 1080x1920
    # 4. Draw divider bar and accent lines
    # 5. Draw dynamic banner text
    # 6. Draw dynamic kinetic captions
    filter_chains = [
        "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1[top]",
        "[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1[bottom]",
        "[top][bottom]vstack=inputs=2[stacked]",
        # Center divider background box
        f"[stacked]drawbox=x=0:y={div_y1}:w=1080:h={divider_height}:color={divider_color}:t=fill[d0]",
        # Accent top border line on divider
        f"[d0]drawbox=x=0:y={div_y1}:w=1080:h={border_width}:color={border_color}:t=fill[d1]",
        # Accent bottom border line on divider
        f"[d1]drawbox=x=0:y={div_y2 - border_width}:w=1080:h={border_width}:color={border_color}:t=fill[base]"
    ]

    drawtext_ops = []

    # Banners on divider bar
    if banners:
        for b in banners:
            text = b.get("text", "").replace("'", "\\'").replace(":", "\\:")
            start = b.get("start", 0.0)
            end = b.get("end", 999.0)
            color = b.get("color", "#FFE600")
            size = b.get("size", 48)
            # Center vertically on the divider bar
            y_pos = div_y1 + (divider_height - size) // 2 - 2
            drawtext_ops.append(
                f"drawtext=fontfile='{font_path}':text='{text}':fontcolor={color}:"
                f"fontsize={size}:x=(w-text_w)/2:y={y_pos}:"
                f"bordercolor=black:borderw=4:enable='between(t,{start:.2f},{end:.2f})'"
            )

    # Kinetic captions in presenter area or lower-middle
    if captions:
        for c in captions:
            text = c.get("text", "").replace("'", "\\'").replace(":", "\\:")
            start = c.get("start", 0.0)
            end = c.get("end", 999.0)
            color = c.get("color", "white")
            size = c.get("size", 54)
            y_pos = c.get("y", 1040)
            drawtext_ops.append(
                f"drawtext=fontfile='{font_path}':text='{text}':fontcolor={color}:"
                f"fontsize={size}:x=(w-text_w)/2:y={y_pos}:"
                f"bordercolor=black:borderw=5:enable='between(t,{start:.2f},{end:.2f})'"
            )

    if drawtext_ops:
        filter_complex = ";".join(filter_chains) + f";[base]{','.join(drawtext_ops)}[v]"
    else:
        filter_complex = ";".join(filter_chains) + f";[base]null[v]"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(top_video),
        "-stream_loop", "-1",
        "-i", str(bottom_video),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{audio_duration:.3f}",
        "-shortest",
        str(output_path)
    ]

    print(f"[*] Executing Top/Down render to {output_path}...")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(f"[!] ffmpeg failed with code {proc.returncode}:\n{proc.stderr}")
        return False

    print(f"[+] Successfully rendered Top/Down split video: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Render a 9:16 top/down split video.")
    parser.add_argument("--top-video", required=True, help="Path to top background/story video")
    parser.add_argument("--bottom-video", required=True, help="Path to bottom presenter video")
    parser.add_argument("--audio", required=True, help="Path to voiceover audio track")
    parser.add_argument("--output", required=True, help="Path to output MP4")
    parser.add_argument("--manifest", help="Optional JSON manifest with beats and captions")
    parser.add_argument("--divider-height", type=int, default=76, help="Divider bar height in pixels")

    args = parser.parse_args()

    top_vid = Path(args.top_video)
    bot_vid = Path(args.bottom_video)
    aud = Path(args.audio)
    out = Path(args.output)

    banners = []
    captions = []

    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.is_file():
            parser.error(f"Manifest file not found: {manifest_path}")
        with open(manifest_path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            parser.error("Manifest JSON must be an object")
        banners = data.get("banners", [])
        captions = data["captions"] if "captions" in data else data.get("beats", [])

    success = render_top_down_split(
        top_video=top_vid,
        bottom_video=bot_vid,
        audio_path=aud,
        output_path=out,
        banners=banners,
        captions=captions,
        divider_height=args.divider_height
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
