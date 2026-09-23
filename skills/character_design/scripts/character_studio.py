#!/usr/bin/env python3
"""
Character Studio CLI - Dynamic Character Director & Looks for Video
Companion to https://daily-character-studio.higgsfield.app/

Instead of relying solely on static deterministic presets, this CLI acts as an
AI Character Director: dynamically synthesizing hairstyles, outfits, environments,
lighting, camera optics, and expressions from any freeform creative brief or script,
while anchoring permanent facial identity for video generation.
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
from typing import Dict, Any, List, Optional

# Ensure scripts dir is on sys.path for direct invocation
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from studio_data import (
    SEED_REFERENCE,
    DEFAULT_SETTINGS,
    PRESETS,
    get_preset,
    synthesize_look_from_brief,
    synthesize_story_pack,
    image_prompt,
    motion_prompt,
)


def find_higgsfield_bin() -> Optional[str]:
    """Find the higgsfield executable in PATH or standard installation paths."""
    candidates = [
        shutil.which("higgsfield"),
        os.path.expanduser("~/.local/bin/higgsfield"),
        "/usr/local/bin/higgsfield",
        "/opt/homebrew/bin/higgsfield",
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def execute_cmd(cmd: List[str], dry_run: bool = False) -> Optional[str]:
    """Execute a CLI command or print if in dry-run mode."""
    cmd_str = " ".join(cmd)
    if dry_run:
        print(f"\n[DRY RUN] Would execute:\n{cmd_str}\n")
        return None

    print(f"\n🚀 Executing:\n{cmd_str}\n")
    try:
        proc = subprocess.run(cmd, check=True, text=True, capture_output=False)
        return "success"
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with return code {e.returncode}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("❌ Higgsfield CLI executable not found.", file=sys.stderr)
        return None


def resolve_character_settings(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Intelligently resolve character settings:
    1. If --brief is provided, dynamically synthesize all attributes from the creative brief.
    2. If --preset is provided, seed from that preset.
    3. Otherwise seed from DEFAULT_SETTINGS.
    4. Layer any explicit CLI flag overrides on top.
    """
    overrides = {}
    for key in [
        "hair", "outfit", "location", "activity", "framing",
        "expression", "lighting", "lens", "accessories", "notes"
    ]:
        val = getattr(args, key, None)
        if val is not None and str(val).strip():
            overrides[key] = val

    ar = getattr(args, "aspect_ratio", None)
    if ar:
        overrides["aspectRatio"] = ar

    brief = getattr(args, "brief", None) or getattr(args, "scenario", None)
    if brief and brief.strip():
        # Dynamic agent-driven synthesis from creative brief
        settings = synthesize_look_from_brief(
            brief=brief,
            overrides=overrides,
            aspect_ratio=overrides.get("aspectRatio", "9:16")
        )
        return settings

    # Preset-based or default fallback
    settings = dict(DEFAULT_SETTINGS)
    preset_name = getattr(args, "preset", None)
    if preset_name:
        preset_def = get_preset(preset_name)
        if preset_def:
            settings.update(preset_def["settings"])
        else:
            print(f"⚠️ Warning: Preset '{preset_name}' not found. Using defaults.", file=sys.stderr)

    settings.update(overrides)
    return settings


def cmd_list_presets(args: argparse.Namespace) -> None:
    """List built-in inspirational look archetypes."""
    print("=" * 70)
    print("✨ DAILY CHARACTER STUDIO — INSPIRATIONAL LOOK PRESETS")
    print("💡 Note: You can also pass any freeform --brief to synthesize custom looks!")
    print("=" * 70)
    for p in PRESETS:
        s = p["settings"]
        print(f"\n🔹 ID: [{p['id']}] — {p['title']}")
        print(f"   Theme:       {p['prompt']}")
        print(f"   Hair:        {s.get('hair')}")
        print(f"   Outfit:      {s.get('outfit')}")
        print(f"   Location:    {s.get('location')}")
        print(f"   Activity:    {s.get('activity')}")
        print(f"   Framing:     {s.get('framing')} | Expression: {s.get('expression')}")
        print(f"   Lighting:    {s.get('lighting')}")
    print("\n" + "=" * 70)


def cmd_prompt(args: argparse.Namespace) -> None:
    """Compile and preview prompt text and CLI commands without running generation."""
    settings = resolve_character_settings(args)
    mode = getattr(args, "mode", "new").lower()
    ref_image = getattr(args, "reference_image", None) or SEED_REFERENCE["id"]
    approved_image = getattr(args, "approved_image", None)

    print("=" * 70)
    print(f"📋 CHARACTER STUDIO DYNAMIC PROMPT COMPILER (Mode: {mode.upper()})")
    print("=" * 70)

    if mode in ("animate", "video"):
        motion_dir = getattr(args, "motion", None)
        if not motion_dir and getattr(args, "brief", None):
            motion_dir = f"Subject portrays: {args.brief}. Natural breathing, organic movement."
        elif not motion_dir and getattr(args, "preset", None):
            p = get_preset(args.preset)
            if p and "animation" in p:
                motion_dir = p["animation"].get("motion")

        prompt_str = motion_prompt(
            motion_direction=motion_dir,
            framing=settings.get("framing", "Waist-up"),
            expression=settings.get("expression", "Relaxed smile"),
            activity=settings.get("activity", "portrait")
        )
        duration = getattr(args, "duration", 5)
        ar = settings.get("aspectRatio", "9:16")

        print(f"\n[Generated Seedance 2.5 Video Motion Prompt]:\n{prompt_str}\n")
        print(f"Duration:     {duration}s")
        print(f"Aspect Ratio: {ar}")
        print(f"Start Image:  {approved_image or '<approved_look.png>'}")

        hf_bin = find_higgsfield_bin() or "higgsfield"
        cli_cmd = [
            hf_bin, "generate", "create", "seedance_2_5",
            "--prompt", f'"{prompt_str}"',
            "--mode", "omni_reference",
            "--start-image", approved_image or "<approved_look.png>",
            "--duration", str(duration),
            "--aspect_ratio", ar,
            "--resolution", "720p",
            "--wait"
        ]
        print(f"\n[Higgsfield CLI Command]:\n{' '.join(cli_cmd)}\n")
    else:
        prompt_str = image_prompt(settings, mode=mode)
        ar = settings.get("aspectRatio", "9:16")

        print("\n[Synthesized Character Styling Blueprint]:")
        print(f"   Hair:        {settings.get('hair')}")
        print(f"   Outfit:      {settings.get('outfit')}")
        print(f"   Location:    {settings.get('location')}")
        print(f"   Activity:    {settings.get('activity')}")
        print(f"   Lighting:    {settings.get('lighting')}")
        print(f"   Camera Lens: {settings.get('lens')}")
        print(f"   Expression:  {settings.get('expression')}")

        print(f"\n[Generated Look Image Prompt (Anti-Drift Identity Anchor)]:\n{prompt_str}\n")
        print(f"Aspect Ratio: {ar}")
        print(f"Reference 1 (Identity): {ref_image}")
        if mode in ("hair", "outfit") and approved_image:
            print(f"Reference 2 (Scene Base): {approved_image}")

        hf_bin = find_higgsfield_bin() or "higgsfield"
        cli_cmd = [
            hf_bin, "generate", "create", "gpt_image_2_5",
            "--prompt", f'"{prompt_str}"',
            "--image", ref_image,
        ]
        if mode in ("hair", "outfit") and approved_image:
            cli_cmd.extend(["--image", approved_image])
        cli_cmd.extend([
            "--aspect_ratio", ar,
            "--resolution", "2k",
            "--wait"
        ])
        print(f"\n[Higgsfield CLI Command]:\n{' '.join(cli_cmd)}\n")

    if getattr(args, "json", False):
        payload = {
            "mode": mode,
            "settings": settings,
            "prompt": prompt_str,
            "reference_image": ref_image,
            "approved_image": approved_image,
        }
        print(json.dumps(payload, indent=2))


def cmd_generate_look(args: argparse.Namespace) -> None:
    """Generate a character look image using the Higgsfield CLI."""
    settings = resolve_character_settings(args)
    prompt_str = image_prompt(settings, mode="new")
    ref_image = getattr(args, "reference_image", None) or SEED_REFERENCE["id"]
    ar = settings.get("aspectRatio", "9:16")
    model = getattr(args, "model", "gpt_image_2_5")

    hf_bin = find_higgsfield_bin()
    if not hf_bin and not args.dry_run:
        print("❌ 'higgsfield' CLI not found. Install via: curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh", file=sys.stderr)
        sys.exit(1)

    cmd = [
        hf_bin or "higgsfield",
        "generate", "create", model,
        "--prompt", prompt_str,
        "--image", ref_image,
        "--aspect_ratio", ar,
        "--resolution", "2k",
        "--wait"
    ]

    execute_cmd(cmd, dry_run=args.dry_run)


def cmd_edit_look(args: argparse.Namespace) -> None:
    """Edit hairstyle or outfit of an approved look image."""
    edit_type = args.edit_type.lower()
    if edit_type not in ("hair", "outfit"):
        print("❌ --edit-type must be either 'hair' or 'outfit'", file=sys.stderr)
        sys.exit(1)

    if not args.approved_image:
        print("❌ --approved-image is required for editing a look", file=sys.stderr)
        sys.exit(1)

    settings = resolve_character_settings(args)
    prompt_str = image_prompt(settings, mode=edit_type)
    ref_image = getattr(args, "reference_image", None) or SEED_REFERENCE["id"]
    ar = settings.get("aspectRatio", "9:16")
    model = getattr(args, "model", "gpt_image_2_5")

    hf_bin = find_higgsfield_bin()
    if not hf_bin and not args.dry_run:
        print("❌ 'higgsfield' CLI not found in PATH or ~/.local/bin", file=sys.stderr)
        sys.exit(1)

    cmd = [
        hf_bin or "higgsfield",
        "generate", "create", model,
        "--prompt", prompt_str,
        "--image", ref_image,
        "--image", args.approved_image,
        "--aspect_ratio", ar,
        "--resolution", "2k",
        "--wait"
    ]

    execute_cmd(cmd, dry_run=args.dry_run)


def cmd_animate_look(args: argparse.Namespace) -> None:
    """Animate an approved look into a Seedance 2.5 video clip."""
    if not args.approved_image:
        print("❌ --approved-image is required to animate a look", file=sys.stderr)
        sys.exit(1)

    settings = resolve_character_settings(args)
    motion_dir = getattr(args, "motion", None)
    if not motion_dir and getattr(args, "brief", None):
        motion_dir = f"Character executes: {args.brief}. Natural breathing, subtle micro-expressions."
    elif not motion_dir and getattr(args, "preset", None):
        p = get_preset(args.preset)
        if p and "animation" in p:
            motion_dir = p["animation"].get("motion")

    prompt_str = motion_prompt(
        motion_direction=motion_dir,
        framing=settings.get("framing", "Waist-up"),
        expression=settings.get("expression", "Relaxed smile"),
        activity=settings.get("activity", "portrait")
    )
    duration = getattr(args, "duration", 5)
    ar = settings.get("aspect_ratio", None) or settings.get("aspectRatio", "9:16")
    model = getattr(args, "model", "seedance_2_5")

    hf_bin = find_higgsfield_bin()
    if not hf_bin and not args.dry_run:
        print("❌ 'higgsfield' CLI not found in PATH or ~/.local/bin", file=sys.stderr)
        sys.exit(1)

    cmd = [
        hf_bin or "higgsfield",
        "generate", "create", model,
        "--prompt", prompt_str,
        "--mode", "omni_reference",
        "--start-image", args.approved_image,
        "--duration", str(duration),
        "--aspect_ratio", ar,
        "--resolution", "720p",
        "--wait"
    ]

    execute_cmd(cmd, dry_run=args.dry_run)


def cmd_pack(args: argparse.Namespace) -> None:
    """Dynamically generate a multi-scene character wardrobe pack for video creation."""
    brief = getattr(args, "brief", None) or getattr(args, "theme", "creator_day_in_life")
    ref_image = getattr(args, "reference_image", None) or SEED_REFERENCE["id"]
    scenes_count = getattr(args, "scenes", 5)

    print("=" * 70)
    print(f"📦 DYNAMIC MULTI-SCENE CHARACTER WARDROBE PACK: {brief.upper()}")
    print("=" * 70)

    manifest = synthesize_story_pack(
        story_brief=brief,
        scene_count=scenes_count,
        identity_ref=ref_image
    )

    for item in manifest["scenes"]:
        print(f"\n🎬 [{item['scene_id']}] {item['title']}")
        print(f"   Style:  {item['settings'].get('hair')} | {item['settings'].get('outfit')}")
        print(f"   Venue:  {item['settings'].get('location')}")
        print(f"   Light:  {item['settings'].get('lighting')}")
        print(f"   Image:  {item['image_prompt'][:110]}...")
        print(f"   Motion: {item['video_prompt'][:110]}...")

    output_path = getattr(args, "output", "character_wardrobe_pack.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n💾 Saved complete production pack manifest to: {output_path}")
    print("👉 Ready for batch rendering via Seedance 2.5 or seedance_video_deconstructor!\n")


def cmd_save_look(args: argparse.Namespace) -> None:
    """Save an approved look recipe to local catalog."""
    catalog_path = getattr(args, "catalog", "looks_catalog.json")
    catalog: List[Dict[str, Any]] = []
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            catalog = []

    settings = resolve_character_settings(args)
    look_entry = {
        "id": getattr(args, "name", "look_" + str(len(catalog) + 1)).lower().replace(" ", "_"),
        "name": getattr(args, "name", f"Look {len(catalog) + 1}"),
        "reference_image": getattr(args, "reference_image", None) or SEED_REFERENCE["id"],
        "approved_image": getattr(args, "approved_image", None),
        "settings": settings,
        "image_prompt": image_prompt(settings, mode="new"),
        "motion_prompt": motion_prompt(
            motion_direction=getattr(args, "motion", None),
            framing=settings.get("framing", "Waist-up"),
            expression=settings.get("expression", "Relaxed smile"),
            activity=settings.get("activity", "portrait")
        )
    }

    catalog.append(look_entry)
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"✅ Saved look '{look_entry['name']}' to {catalog_path}")


def cmd_list_looks(args: argparse.Namespace) -> None:
    """List saved looks from local catalog."""
    catalog_path = getattr(args, "catalog", "looks_catalog.json")
    if not os.path.exists(catalog_path):
        print(f"No catalog found at {catalog_path}. Use 'save-look' to create one.")
        return

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print("=" * 70)
    print(f"📖 SAVED CHARACTER LOOKS ({len(catalog)} total)")
    print("=" * 70)
    for look in catalog:
        s = look.get("settings", {})
        print(f"\n👗 [{look.get('id')}] {look.get('name')}")
        print(f"   Hair:     {s.get('hair')}")
        print(f"   Outfit:   {s.get('outfit')}")
        print(f"   Location: {s.get('location')}")
        print(f"   Approved: {look.get('approved_image') or 'None'}")


def main():
    parser = argparse.ArgumentParser(
        description="Character Studio CLI - Style consistent characters & animate looks for video."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Global options helper
    def add_common_styling_args(p):
        p.add_argument("--brief", "--scenario", dest="brief", help="Freeform creative brief or scenario description")
        p.add_argument("--preset", help="Base preset archetype (e.g. cafe, office, home, podcast, fitness, rooftop)")
        p.add_argument("--hair", help="Hairstyle specification or override")
        p.add_argument("--outfit", help="Wardrobe / outfit specification or override")
        p.add_argument("--location", help="Location / environment specification or override")
        p.add_argument("--activity", help="Activity or kinetic action specification")
        p.add_argument("--framing", help="Framing (Waist-up, Full body, Selfie, Close-up)")
        p.add_argument("--expression", help="Expression / emotional nuance")
        p.add_argument("--lighting", help="Lighting direction, color temperature, and ambience")
        p.add_argument("--lens", help="Camera lens and depth of field specification")
        p.add_argument("--accessories", help="Accessories or props specification")
        p.add_argument("--notes", help="Extra direction notes")
        p.add_argument("--aspect-ratio", choices=["9:16", "16:9", "1:1"], default="9:16", help="Aspect ratio")
        p.add_argument("--reference-image", help="Permanent identity reference image (path or UUID)")
        p.add_argument("--approved-image", help="Approved look image for edits or video start frame")

    # Subcommand: list-presets
    p_presets = subparsers.add_parser("list-presets", help="List built-in inspirational presets")
    p_presets.set_defaults(func=cmd_list_presets)

    # Subcommand: prompt
    p_prompt = subparsers.add_parser("prompt", help="Compile and preview prompt & CLI commands")
    add_common_styling_args(p_prompt)
    p_prompt.add_argument("--mode", choices=["new", "hair", "outfit", "animate"], default="new", help="Generation mode")
    p_prompt.add_argument("--motion", help="Custom video motion prompt for animate mode")
    p_prompt.add_argument("--duration", type=int, default=5, help="Video duration in seconds")
    p_prompt.add_argument("--json", action="store_true", help="Output JSON format")
    p_prompt.set_defaults(func=cmd_prompt)

    # Subcommand: generate-look
    p_gen = subparsers.add_parser("generate-look", help="Generate a new character look image")
    add_common_styling_args(p_gen)
    p_gen.add_argument("--model", default="gpt_image_2_5", help="Image model (default: gpt_image_2_5)")
    p_gen.add_argument("--dry-run", action="store_true", help="Print command without executing")
    p_gen.set_defaults(func=cmd_generate_look)

    # Subcommand: edit-look
    p_edit = subparsers.add_parser("edit-look", help="Edit hairstyle or outfit of an approved look")
    add_common_styling_args(p_edit)
    p_edit.add_argument("--edit-type", required=True, choices=["hair", "outfit"], help="What to edit")
    p_edit.add_argument("--model", default="gpt_image_2_5", help="Image model (default: gpt_image_2_5)")
    p_edit.add_argument("--dry-run", action="store_true", help="Print command without executing")
    p_edit.set_defaults(func=cmd_edit_look)

    # Subcommand: animate-look
    p_anim = subparsers.add_parser("animate-look", help="Animate an approved look into a Seedance 2.5 video clip")
    add_common_styling_args(p_anim)
    p_anim.add_argument("--motion", help="Motion direction")
    p_anim.add_argument("--duration", type=int, default=5, help="Duration in seconds (4-15)")
    p_anim.add_argument("--model", default="seedance_2_5", help="Video model (default: seedance_2_5)")
    p_anim.add_argument("--dry-run", action="store_true", help="Print command without executing")
    p_anim.set_defaults(func=cmd_animate_look)

    # Subcommand: pack
    p_pack = subparsers.add_parser("pack", help="Dynamically generate a multi-scene wardrobe pack")
    p_pack.add_argument("--brief", "--theme", dest="brief", default="creator_day_in_life", help="Story brief or theme description")
    p_pack.add_argument("--scenes", type=int, default=5, help="Number of scenes in arc (3-5)")
    p_pack.add_argument("--reference-image", help="Permanent identity reference image")
    p_pack.add_argument("--output", default="character_wardrobe_pack.json", help="Output JSON filepath")
    p_pack.set_defaults(func=cmd_pack)

    # Subcommand: save-look
    p_save = subparsers.add_parser("save-look", help="Save a look to the local catalog")
    add_common_styling_args(p_save)
    p_save.add_argument("--name", required=True, help="Descriptive name for the look")
    p_save.add_argument("--motion", help="Associated video motion prompt")
    p_save.add_argument("--catalog", default="looks_catalog.json", help="Catalog JSON path")
    p_save.set_defaults(func=cmd_save_look)

    # Subcommand: list-looks
    p_looks = subparsers.add_parser("list-looks", help="List saved looks from catalog")
    p_looks.add_argument("--catalog", default="looks_catalog.json", help="Catalog JSON path")
    p_looks.set_defaults(func=cmd_list_looks)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
