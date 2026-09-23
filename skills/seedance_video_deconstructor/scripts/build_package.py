#!/usr/bin/env python3
"""
Automated Package Generator for Seedance 2.5 Production Packs
Generates directory structure, prompt manifests, cut sheet CSVs, README,
downloads public-domain archival reference imagery, and creates a zipped bundle.
"""

import os
import sys
import json
import csv
import zipfile
import urllib.request
import argparse
from typing import Dict, Any, List

DEFAULT_BUNDLE_DIR = "bikini_police_seedance_workflow"
DEFAULT_ZIP = "bikini_police_seedance_workflow.zip"

DEFAULT_PROMPTS_DATA: Dict[str, Any] = {
    "project": "Dylan Page Style - Bikini Police Hook Ad",
    "engine": "Seedance 2.5",
    "global_settings": {
        "aspect_ratio": "9:16",
        "fps": 30,
        "default_duration": "5s",
        "r2v_reference_strength": 0.75
    },
    "shots": [
        {
            "shot_id": "shot_01_hook",
            "name": "The Beach Police Measuring Hook",
            "duration": "4s",
            "reference_image": "reference_images/ref1_beach_censor_1922.jpg",
            "prompt": "Cinematic 1920s archival documentary footage, authentic black-and-white 35mm film grain, high contrast. A serious, stern male police officer kneeling on the sand, measuring the hemline of a woman's swimsuit with a wooden ruler. Beachgoers watching in the background. Wide establishing shot, slow push-in. --ar 9:16 --motion 4"
        },
        {
            "shot_id": "shot_02_macro",
            "name": "Macro Tape Measure Detail",
            "duration": "5s",
            "reference_image": "reference_images/ref1_beach_censor_1922.jpg",
            "prompt": "Extreme close-up macro shot, vintage 1930s monochrome photography. A weathered pair of hands holding a yellowed fabric measuring tape against the edge of a wool bathing suit hem on a sandy beach. Shallow depth of field, subtle hand tremble. --ar 9:16 --motion 3"
        },
        {
            "shot_id": "shot_03_arrest",
            "name": "Beach Boardwalk Escort",
            "duration": "5s",
            "reference_image": None,
            "prompt": "Mid-shot tracking scene, vintage 1940s newsreel film aesthetic, authentic silver-halide grain. Two uniformed patrolmen firmly escorting an indignant woman in a vintage swimsuit across a crowded boardwalk. Bystanders turn and whisper. --ar 9:16 --motion 5"
        },
        {
            "shot_id": "shot_04_bikini_reveal",
            "name": "1946 Paris Fashion Reveal",
            "duration": "6s",
            "reference_image": None,
            "prompt": "1946 Parisian fashion presentation at Piscine Molitor public swimming pool, vintage Technicolor 3-strip aesthetic. A glamorous French model poses courageously in a revolutionary newspaper-printed two-piece bikini as vintage press photographers with flashbulb cameras burst flashes. --ar 9:16 --motion 4"
        },
        {
            "shot_id": "shot_05_punchline",
            "name": "Comic Weary Officer Reaction",
            "duration": "4s",
            "reference_image": "reference_images/ref1_beach_censor_1922.jpg",
            "prompt": "Medium close-up portrait, 1920s archival documentary aesthetic. A vintage beach patrol officer looking directly into the lens with an exhausted, deadpan, bewildered expression, holding a measuring tape limply. Subtle comedic slow zoom-in. --ar 9:16 --motion 2"
        }
    ]
}

DEFAULT_TIMELINE_DATA: List[List[str]] = [
    ["Timeline (Sec)", "Shot ID", "Spoken Script", "On-Screen Text Hook", "Sound Effects / Audio Cues"],
    ["0:00 - 0:04", "shot_01_hook", "Being a bikini police officer was actually a real 9-to-5 job... and it was just as unhinged as you think.", "BIKINI POLICE WAS A REAL JOB?! (Yellow/white bold)", "Camera shutter snap, tape measure pull"],
    ["0:04 - 0:10", "shot_01_hook", "Back in the 1920s through the 1950s, modesty laws on public beaches were insanely strict. Your bathing suit could not be more than a few inches above the knee.", "STRICT LAWS / MEASURING TAPES", "Gentle ocean surf, beach crowd murmur"],
    ["0:10 - 0:17", "shot_02_macro", "Special beach censors and 'bathing police' literally patrolled the sand with tape measures to make sure women weren't showing 'too much thigh'.", "MEASURING THIGHS ON THE BEACH", "Tape measure click, quiet whispering"],
    ["0:17 - 0:24", "shot_03_arrest", "If you were even two inches too short? You didn't just get a warning. You got hit with massive fines or literally dragged straight to jail right off the sand.", "ARRESTED (Red stamp)", "Heavy footsteps, crowd gasp, whoosh"],
    ["0:24 - 0:33", "shot_04_bikini_reveal", "Then in 1946, French engineer Louis Réard dropped the modern bikini—named after Bikini Atoll nuclear tests because he knew it would cause an explosion. Models literally refused to wear it.", "TOO SCANDALOUS (Vintage headline)", "Flashbulb pops, vintage jazz trumpet"],
    ["0:33 - 0:42", "shot_05_punchline", "Imagine having to tell your grandkids that your government job was measuring swimsuits with a ruler. Follow for more crazy history.", "WORST JOB IN HISTORY? + Follow pulse", "Comedic violin pluck or record scratch"]
]

README_TEMPLATE = """# Bikini Police Viral Short - Seedance 2.5 Production Pack

## Directory Structure
- `/configs/seedance_prompts.json`: API & batch execution prompt list.
- `/configs/timeline_cutsheet.csv`: CapCut/Premiere timeline sync sheet.
- `/reference_images/`: Archival source imagery for Seedance R2V / I2V mode.

## Seedance 2.5 Recommended Settings
- **Mode:** Reference-to-Video (R2V)
- **Fidelity Weight:** 0.75
- **Aspect Ratio:** 9:16 (1080x1920)
- **Resolution:** High (Enhance Skin/Grain)
- **Audio Generation:** Synchronized Foley Enabled

## Post-Production Retention Guide
1. **Talking-Head Picture-in-Picture (PiP):** Narration green-screened in lower-third, pointing up at Seedance footage.
2. **Kinetic Captions:** TheBoldFont / Montserrat Black, 1-3 words center-screen, `#FFE600` yellow / red flashes.
3. **Sound Design Stacking:** Mystery bed ducked -18 dB behind voice, shutter snap on visual transitions.
"""

IMAGES_TO_DOWNLOAD = [
    {
        "filename": "ref1_beach_censor_1922.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Beach_censor_1922.jpg/800px-Beach_censor_1922.jpg"
    }
]


def build_package(bundle_dir: str, zip_filename: str, skip_download: bool = False):
    print(f"📦 Assembling Seedance 2.5 production bundle in: {bundle_dir}")
    os.makedirs(os.path.join(bundle_dir, "reference_images"), exist_ok=True)
    os.makedirs(os.path.join(bundle_dir, "configs"), exist_ok=True)

    # 1. Write Prompt Manifest
    prompt_path = os.path.join(bundle_dir, "configs", "seedance_prompts.json")
    with open(prompt_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PROMPTS_DATA, f, indent=2)
    print(f"  ✓ Wrote prompt manifest: {prompt_path}")

    # 2. Write Timeline Cut Sheet & Narration CSV
    csv_path = os.path.join(bundle_dir, "configs", "timeline_cutsheet.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(DEFAULT_TIMELINE_DATA)
    print(f"  ✓ Wrote timeline cut sheet: {csv_path}")

    # 3. Write README and Workflow Guide
    readme_path = os.path.join(bundle_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(README_TEMPLATE)
    print(f"  ✓ Wrote workflow guide: {readme_path}")

    # 4. Download Public Domain Archival Reference Images
    if not skip_download:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
        for item in IMAGES_TO_DOWNLOAD:
            dest_path = os.path.join(bundle_dir, "reference_images", item["filename"])
            try:
                req = urllib.request.Request(item["url"], headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp, open(dest_path, "wb") as out:
                    out.write(resp.read())
                print(f"  ✓ Downloaded reference image: {item['filename']}")
            except Exception as e:
                print(f"  ⚠ Could not download {item['filename']} ({e}); continuing with offline placeholder.")
                # Touch empty placeholder so structure exists
                with open(dest_path, "wb") as out:
                    out.write(b"")

    # 5. Compress into .zip
    print(f"🗜 Compressing bundle into: {zip_filename}")
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(bundle_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=bundle_dir)
                zipf.write(full_path, arcname)

    print(f"✨ Successfully created archive: {zip_filename}\n")


def main():
    parser = argparse.ArgumentParser(description="Build Seedance 2.5 production package zip bundle.")
    parser.add_argument("--bundle-dir", default=DEFAULT_BUNDLE_DIR, help="Output directory for bundle files")
    parser.add_argument("--zip-name", default=DEFAULT_ZIP, help="Filename of the compressed .zip bundle")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading external reference images")

    args = parser.parse_args()
    build_package(bundle_dir=args.bundle_dir, zip_filename=args.zip_name, skip_download=args.skip_download)


if __name__ == "__main__":
    main()
