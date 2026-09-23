#!/usr/bin/env python3
"""
CLI Video Generator for Seedance via Higgsfield AI
Executes text-to-video and reference-to-video generation for single shots or batch manifests.
Supports Seedance 2.5 (Pro/Ultimate plans) and Seedance 1.5 Pro / Kling 3.0 (Starter plan).
"""

import sys
import os
import json
import subprocess
import shutil
import argparse
from typing import Dict, Any, List, Optional


def check_higgsfield_cli() -> bool:
    """Verify that higgsfield CLI is installed and in PATH."""
    return shutil.which("higgsfield") is not None


def build_higgsfield_command(
    prompt: str,
    model: str = "seedance_2_5",
    aspect_ratio: str = "9:16",
    duration: int = 5,
    resolution: str = "720p",
    reference_image: Optional[str] = None,
    wait: bool = True
) -> List[str]:
    """Construct the exact higgsfield generate create command."""
    # Clean up prompt formatting if it contains CLI flags
    clean_prompt = prompt.split("--ar")[0].split("--motion")[0].strip()

    cmd = [
        "higgsfield",
        "generate",
        "create",
        model,
        "--prompt", clean_prompt,
        "--aspect_ratio", aspect_ratio,
        "--duration", str(duration),
        "--resolution", resolution,
    ]

    if model in ("seedance_2_5", "seedance_2_0"):
        if reference_image and os.path.exists(reference_image):
            cmd.extend(["--mode", "omni_reference", "--image", reference_image])
        else:
            cmd.extend(["--mode", "t2v"])
    elif model == "seedance1_5":
        if reference_image and os.path.exists(reference_image):
            cmd.extend(["--start-image", reference_image])
    elif "kling" in model:
        if reference_image and os.path.exists(reference_image):
            cmd.extend(["--start-image", reference_image])

    if wait:
        cmd.append("--wait")

    return cmd


def run_shot_generation(
    shot: Dict[str, Any],
    model: str = "seedance_2_5",
    aspect_ratio: str = "9:16",
    resolution: str = "720p",
    base_dir: str = ".",
    dry_run: bool = False
) -> Optional[str]:
    """Generate a single shot using Higgsfield CLI."""
    shot_id = shot.get("shot_id", "unnamed_shot")
    prompt = shot.get("prompt", "")
    duration_str = str(shot.get("duration", "5s")).replace("s", "")
    try:
        duration = int(duration_str)
    except ValueError:
        duration = 5

    # Seedance 1.5 only supports 4, 8, 12
    if model == "seedance1_5" and duration not in (4, 8, 12):
        duration = 4 if duration <= 6 else (8 if duration <= 10 else 12)

    ref_img = shot.get("reference_image")
    if ref_img and not os.path.isabs(ref_img):
        ref_img = os.path.join(base_dir, ref_img)

    cmd = build_higgsfield_command(
        prompt=prompt,
        model=model,
        aspect_ratio=aspect_ratio,
        duration=duration,
        resolution=resolution,
        reference_image=ref_img if (ref_img and os.path.exists(ref_img)) else None,
        wait=True
    )

    print(f"\n🎬 Generating {shot_id.upper()} ({model}, {duration}s, {aspect_ratio}):")
    print(f"   Command: {' '.join(cmd)}")

    if dry_run:
        print("   [DRY-RUN] Skipped API execution.")
        return "dry_run_preview_url"

    if not check_higgsfield_cli():
        print("❌ Error: 'higgsfield' CLI is not found on PATH.")
        print("Install via: curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh")
        return None

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = proc.stdout.strip()
        print(f"   ✓ Completed: {out}")
        return out
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Generation failed (exit code {e.returncode}):")
        if e.stderr:
            print(f"      {e.stderr.strip()}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Seedance Video Generation CLI via Higgsfield AI"
    )
    parser.add_argument("--manifest", type=str, help="Path to seedance_prompts.json manifest")
    parser.add_argument("--shot", type=str, help="Specific shot_id to generate (e.g. shot_01_hook)")
    parser.add_argument("--all", action="store_true", help="Generate all shots in manifest sequentially")
    parser.add_argument("--model", type=str, default="seedance_2_5", help="Model ID (seedance_2_5, seedance1_5, kling3_0_turbo)")
    parser.add_argument("--prompt", type=str, help="Direct prompt string for ad-hoc generation")
    parser.add_argument("--image", type=str, default=None, help="Reference image path for R2V mode")
    parser.add_argument("--duration", type=int, default=5, help="Clip duration in seconds")
    parser.add_argument("--aspect-ratio", type=str, default="9:16", choices=["9:16", "16:9", "1:1"])
    parser.add_argument("--resolution", type=str, default="720p", choices=["480p", "720p", "1080p"])
    parser.add_argument("--dry-run", action="store_true", help="Preview Higgsfield CLI commands without charging credits")

    args = parser.parse_args()

    # Case 1: Ad-hoc direct prompt
    if args.prompt:
        shot = {
            "shot_id": "custom_shot",
            "prompt": args.prompt,
            "duration": args.duration,
            "reference_image": args.image
        }
        run_shot_generation(
            shot=shot,
            model=args.model,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            dry_run=args.dry_run
        )
        return

    # Case 2: Manifest-based generation
    if args.manifest:
        if not os.path.exists(args.manifest):
            print(f"Error: Manifest file not found: {args.manifest}")
            sys.exit(1)

        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        global_settings = manifest_data.get("global_settings", {})
        aspect_ratio = args.aspect_ratio or global_settings.get("aspect_ratio", "9:16")
        shots = manifest_data.get("shots", [])
        base_dir = os.path.dirname(os.path.abspath(args.manifest))

        if args.shot:
            matched = [s for s in shots if s.get("shot_id") == args.shot]
            if not matched:
                print(f"Error: Shot '{args.shot}' not found in manifest.")
                sys.exit(1)
            run_shot_generation(
                shot=matched[0],
                model=args.model,
                aspect_ratio=aspect_ratio,
                resolution=args.resolution,
                base_dir=base_dir,
                dry_run=args.dry_run
            )
        elif args.all:
            print(f"🚀 Batch generating {len(shots)} shots for '{manifest_data.get('project', 'Project')}' using {args.model}...")
            results = {}
            for s in shots:
                res = run_shot_generation(
                    shot=s,
                    model=args.model,
                    aspect_ratio=aspect_ratio,
                    resolution=args.resolution,
                    base_dir=base_dir,
                    dry_run=args.dry_run
                )
                results[s.get("shot_id")] = res
            print("\n🏁 Batch generation run complete.")
        else:
            print("Please specify --shot <shot_id>, --all, or --prompt.")
            return

    elif not args.prompt:
        parser.print_help()


if __name__ == "__main__":
    main()
