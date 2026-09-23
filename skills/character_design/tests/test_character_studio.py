"""
Unit tests for the Character Design & Dynamic Look Director skill scripts.
Runs on both pytest and stdlib unittest (zero dependencies).
"""

import sys
import os
import json
import unittest
import tempfile
import subprocess
from pathlib import Path

# Add scripts directory to sys.path
TEST_DIR = Path(__file__).resolve().parent
SKILL_DIR = TEST_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from studio_data import (
    PRESETS,
    SEED_REFERENCE,
    DEFAULT_SETTINGS,
    get_preset,
    synthesize_look_from_brief,
    synthesize_story_pack,
    image_prompt,
    motion_prompt,
)


class TestCharacterStudio(unittest.TestCase):

    def test_preset_definitions(self):
        """Verify that inspirational presets have valid structure."""
        self.assertGreaterEqual(len(PRESETS), 3)
        for p in PRESETS:
            self.assertIn("id", p)
            self.assertIn("title", p)
            self.assertIn("settings", p)
            s = p["settings"]
            self.assertIn(s["aspectRatio"], ("9:16", "16:9", "1:1"))
            if "animation" in p:
                self.assertIn("motion", p["animation"])

    def test_synthesize_look_from_brief_coffee(self):
        """Test synthesizing a look from a coffee shop brief."""
        brief = "A relaxed barista making pour-over coffee in a sunlit Scandinavian cafe on Sunday morning"
        look = synthesize_look_from_brief(brief)

        self.assertIn("coffee", look["location"].lower())
        self.assertIn("mug", look["activity"].lower() + look["accessories"].lower())
        self.assertIn("natural", look["lighting"].lower() + look["hair"].lower())
        self.assertEqual(look["aspectRatio"], "9:16")

    def test_synthesize_look_from_brief_cyberpunk(self):
        """Test synthesizing a look from a futuristic cyberpunk brief."""
        brief = "Cyberpunk courier standing in rain-slicked neo-Tokyo alley at night under neon signs"
        look = synthesize_look_from_brief(brief)

        self.assertIn("neon", look["location"].lower() + look["lighting"].lower())
        self.assertTrue(any(w in look["outfit"].lower() for w in ["jacket", "black", "textile", "technical"]))

    def test_synthesize_look_with_overrides(self):
        """Test that explicit overrides take precedence over synthesized defaults."""
        brief = "Business executive presenting in a boardroom"
        overrides = {
            "hair": "Crimson red asymmetrical bob",
            "outfit": "Emerald green tailored velvet suit",
            "aspectRatio": "16:9"
        }
        look = synthesize_look_from_brief(brief, overrides=overrides)

        self.assertEqual(look["hair"], "Crimson red asymmetrical bob")
        self.assertEqual(look["outfit"], "Emerald green tailored velvet suit")
        self.assertEqual(look["aspectRatio"], "16:9")

    def test_image_prompt_identity_anchor(self):
        """Verify prompt contains strict anti-drift identity clauses."""
        settings = {
            "hair": "Sleek blowout",
            "outfit": "Navy blazer and white top",
            "location": "Modern architectural office",
            "activity": "Speaking to camera",
            "framing": "Close-up",
            "expression": "Confident",
            "lighting": "Diffused soft daylight",
            "lens": "85mm f/1.4 prime lens",
            "accessories": "Small gold hoop earrings",
            "notes": "Crisp morning natural light",
            "aspectRatio": "9:16",
        }
        prompt = image_prompt(settings, mode="new")

        self.assertIn("IDENTITY: The first reference is the permanent identity source.", prompt)
        self.assertIn("Preserve the exact same recognizable facial geometry", prompt)
        self.assertIn("output only one person in one photograph, never a collage", prompt)
        self.assertIn("Hairstyle: Sleek blowout.", prompt)
        self.assertIn("Outfit: Navy blazer and white top.", prompt)
        self.assertIn("Lighting & Atmosphere: Diffused soft daylight.", prompt)
        self.assertIn("Camera Lens: 85mm f/1.4 prime lens.", prompt)
        self.assertIn("No labels, no text overlays, no contact sheet, no watermark", prompt)

    def test_image_prompt_targeted_edits(self):
        """Verify targeted inpainting prompts for hair and outfit."""
        # Hair edit
        hair_prompt = image_prompt({"hair": "Tousled curly bob"}, mode="hair")
        self.assertIn("Edit only the hairstyle of the final reference image.", hair_prompt)
        self.assertIn("Hairstyle: Tousled curly bob.", hair_prompt)

        # Outfit edit
        outfit_prompt = image_prompt({"outfit": "Linen button-down shirt"}, mode="outfit")
        self.assertIn("Edit only the clothing of the final reference image.", outfit_prompt)
        self.assertIn("Outfit: Linen button-down shirt.", outfit_prompt)

    def test_synthesize_story_pack(self):
        """Verify generating a multi-scene narrative wardrobe pack."""
        story = "A wildlife researcher documenting marine life along the Pacific coast"
        pack = synthesize_story_pack(story, scene_count=4)

        self.assertEqual(pack["story_brief"], story)
        self.assertEqual(len(pack["scenes"]), 4)
        for s in pack["scenes"]:
            self.assertIn("scene_id", s)
            self.assertIn("image_prompt", s)
            self.assertIn("video_prompt", s)
            self.assertIn("IDENTITY: The first reference is the permanent identity source.", s["image_prompt"])
            self.assertIn("Use the approved image as the exact first frame.", s["video_prompt"])

    def test_cli_prompt_with_brief(self):
        """Test CLI prompt compiler with dynamic --brief."""
        cli_path = SCRIPTS_DIR / "character_studio.py"
        res = subprocess.run(
            [
                sys.executable, str(cli_path), "prompt",
                "--brief", "An exhausted ER doctor after a 24hr shift sipping tea in the breakroom",
                "--json"
            ],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("CHARACTER STUDIO DYNAMIC PROMPT COMPILER", res.stdout)
        self.assertIn("IDENTITY: The first reference is the permanent identity source.", res.stdout)

    def test_cli_animate_with_brief(self):
        """Test CLI video motion prompt with dynamic --brief."""
        cli_path = SCRIPTS_DIR / "character_studio.py"
        res = subprocess.run(
            [
                sys.executable, str(cli_path), "prompt",
                "--mode", "animate",
                "--approved-image", "approved_doctor.png",
                "--brief", "She slowly rubs her eyes, sighs with relief, and takes a slow sip of tea"
            ],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Use the approved image as the exact first frame.", res.stdout)
        self.assertIn("rubs her eyes", res.stdout)
        self.assertIn("seedance_2_5", res.stdout)

    def test_cli_pack_generation_with_brief(self):
        """Test generating a multi-scene wardrobe pack with --brief."""
        cli_path = SCRIPTS_DIR / "character_studio.py"
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            res = subprocess.run(
                [
                    sys.executable, str(cli_path), "pack",
                    "--brief", "Investigative reporter working on a story in rainy Chicago",
                    "--output", tmp_path
                ],
                capture_output=True,
                text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(tmp_path))

            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("scenes", data)
            self.assertEqual(len(data["scenes"]), 5)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
