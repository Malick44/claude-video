"""End-to-end checks for precise, deterministic cinematic SFX rendering."""

from __future__ import annotations

import array
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/cinematic-sound-designer/scripts/render_cues.py"
SR = 48_000


def write_wav(path: Path, samples: list[int]) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def write_stereo_wav(path: Path, left: int, right: int, frames: int) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(struct.pack(f"<{2 * frames}h", *([left, right] * frames)))


def read_wav_stereo(path: Path) -> tuple[int, int, list[float], list[float]]:
    """Decode either PCM16 or float WAV, reporting amplitudes in PCM16 units."""
    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-c:a",
         "pcm_f32le", "-ac", "2", "-ar", str(SR), "pipe:1"],
        capture_output=True, check=True,
    )
    samples = array.array("f")
    samples.frombytes(decoded.stdout)
    if sys.byteorder != "little":
        samples.byteswap()
    return SR, len(samples) // 2, [sample * 32768 for sample in samples[::2]], [
        sample * 32768 for sample in samples[1::2]
    ]


def read_wav(path: Path) -> tuple[int, int, list[float]]:
    rate, frames, left, _ = read_wav_stereo(path)
    return rate, frames, left


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required")
class RenderCuesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = tempfile.TemporaryDirectory()
        self.root = Path(self.work.name)

    def tearDown(self) -> None:
        self.work.cleanup()

    def run_render(self, manifest: dict, *extra: str) -> subprocess.CompletedProcess[str]:
        cue_json = self.root / "cues.json"
        cue_json.write_text(json.dumps(manifest), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--cues", str(cue_json),
             "--stem", str(self.root / "stem.wav"), *extra],
            capture_output=True, text=True, check=False,
        )

    def test_impulses_land_on_exact_samples_and_relative_paths_resolve(self) -> None:
        sounds = self.root / "sounds"
        sounds.mkdir()
        write_wav(sounds / "click.wav", [12_000] + [0] * 479)
        manifest = {
            "version": 1, "duration_seconds": 0.5,
            "cues": [
                {"id": "one", "at": 0.12345, "asset": "sounds/click.wav",
                 "gain_db": 0, "fade_in_ms": 0, "fade_out_ms": 0,
                 "reason": "first reveal", "tension_before": 2, "tension_after": 6},
                {"id": "two", "at": 0.250, "asset": "sounds/click.wav",
                 "gain_db": -6, "fade_in_ms": 0, "fade_out_ms": 0},
            ],
        }
        result = self.run_render(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["placements"][0]["at_sample"], round(0.12345 * SR))
        self.assertEqual(report["placements"][0]["reason"], "first reveal")
        self.assertEqual(report["placements"][0]["tension_after"], 6)
        rate, frames, left = read_wav(self.root / "stem.wav")
        self.assertEqual((rate, frames), (SR, 24_000))
        nonzero = [index for index, sample in enumerate(left) if sample != 0]
        self.assertEqual(nonzero, [round(0.12345 * SR), 12_000])
        self.assertAlmostEqual(left[nonzero[0]], 12_000, delta=2)
        self.assertAlmostEqual(left[12_000], 12_000 * 10 ** (-6 / 20), delta=2)
        self.assertAlmostEqual(left[12_000] / left[nonzero[0]], 10 ** (-6 / 20), delta=0.01)
        first_render = (self.root / "stem.wav").read_bytes()
        rerun = self.run_render(manifest)
        self.assertEqual(rerun.returncode, 0, rerun.stderr)
        self.assertEqual((self.root / "stem.wav").read_bytes(), first_render)

    def test_sample_fades_and_explicit_timeline_trim(self) -> None:
        write_wav(self.root / "tone.wav", [8_000] * 4_800)
        manifest = {
            "version": 1, "duration_seconds": 0.12,
            "cues": [{"id": "riser", "at": 0.02, "asset": "tone.wav",
                      "gain_db": -3, "fade_in_ms": 10, "fade_out_ms": 20}],
        }
        result = self.run_render(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        _, frames, left = read_wav(self.root / "stem.wav")
        self.assertEqual(frames, 5_760)
        onset = round(0.02 * SR)
        self.assertEqual(left[onset], 0)
        self.assertGreater(abs(left[onset + 1_000]), 1_000)
        self.assertLess(abs(left[-1]), 100)

    def test_mix_has_narration_length_and_peak_limit(self) -> None:
        write_wav(self.root / "impact.wav", [30_000] * 4_800)
        write_wav(self.root / "voice.wav", [25_000] * SR)
        manifest = {
            "version": 1,
            "cues": [{"id": "impact", "at": 0.4, "asset": "impact.wav",
                      "gain_db": 0, "fade_in_ms": 0, "fade_out_ms": 0}],
        }
        result = self.run_render(
            manifest, "--narration", str(self.root / "voice.wav"),
            "--mix", str(self.root / "mix.wav"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        stem_rate, stem_frames, _ = read_wav(self.root / "stem.wav")
        mix_rate, mix_frames, mixed = read_wav(self.root / "mix.wav")
        self.assertEqual((stem_rate, stem_frames), (SR, SR))
        self.assertEqual((mix_rate, mix_frames), (SR, SR))
        self.assertGreater(abs(mixed[0]), 10_000)
        self.assertLessEqual(max(abs(x) for x in mixed), math.ceil(0.891251 * 32768) + 1)

    def test_mono_narration_keeps_peak_in_zero_sfx_mix(self) -> None:
        voice_peak = 9_000
        write_wav(self.root / "voice.wav", [voice_peak] * 4_800)
        result = self.run_render(
            {"version": 1, "duration_seconds": 0.1, "cues": []},
            "--narration", str(self.root / "voice.wav"),
            "--mix", str(self.root / "mix.wav"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        _, _, left = read_wav(self.root / "mix.wav")
        self.assertAlmostEqual(max(left), voice_peak, delta=2)
        _, _, left, right = read_wav_stereo(self.root / "mix.wav")
        self.assertEqual(left, right)

    def test_stereo_cue_keeps_channel_levels(self) -> None:
        write_stereo_wav(self.root / "stereo.wav", 8_000, 4_000, 480)
        manifest = {
            "version": 1,
            "cues": [{"id": "stereo", "at": 0, "asset": "stereo.wav",
                      "gain_db": 0, "fade_in_ms": 0, "fade_out_ms": 0}],
        }
        result = self.run_render(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        _, _, left, right = read_wav_stereo(self.root / "stem.wav")
        self.assertAlmostEqual(max(left), 8_000, delta=2)
        self.assertAlmostEqual(max(right), 4_000, delta=2)

    def test_overlapping_impulses_keep_float_headroom(self) -> None:
        write_wav(self.root / "loud.wav", [28_000] + [0] * 479)
        cue = {"at": 0.01, "asset": "loud.wav", "gain_db": 0,
               "fade_in_ms": 0, "fade_out_ms": 0}
        manifest = {"version": 1, "cues": [{"id": "a", **cue}, {"id": "b", **cue}]}
        result = self.run_render(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertGreater(report["stem_peak_dbfs"], 0)
        self.assertLess(report["stem_headroom_db"], 0)
        _, _, left = read_wav(self.root / "stem.wav")
        self.assertAlmostEqual(left[480], 56_000, delta=4)
        codec = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name",
             "-of", "default=noprint_wrappers=1:nokey=1", str(self.root / "stem.wav")],
            text=True,
        ).strip()
        self.assertEqual(codec, "pcm_f32le")

    def test_audio_duration_ignores_longer_video_container(self) -> None:
        write_wav(self.root / "short.wav", [2_000] * (SR // 2))
        container = self.root / "short_audio_long_video.mkv"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "lavfi", "-i",
             "color=c=black:s=16x16:r=10:d=2", "-i", str(self.root / "short.wav"),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "ffv1", "-c:a",
             "pcm_s16le", str(container)],
            capture_output=True, text=True, check=True,
        )
        manifest = {"version": 1, "cues": [{
            "id": "short", "at": 0, "asset": container.name, "gain_db": 0,
            "fade_in_ms": 0, "fade_out_ms": 0,
        }]}
        result = self.run_render(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(json.loads(result.stdout)["duration_seconds"], 0.5, delta=1 / SR)
        _, frames, _ = read_wav(self.root / "stem.wav")
        self.assertEqual(frames, SR // 2)

    def test_rejects_negative_time_and_fades_longer_than_clip(self) -> None:
        write_wav(self.root / "short.wav", [1_000] * 480)
        cue = {"id": "bad", "at": -0.1, "asset": "short.wav",
               "gain_db": -12, "fade_in_ms": 0, "fade_out_ms": 0}
        result = self.run_render({"version": 1, "cues": [cue]})
        self.assertEqual(result.returncode, 2)
        self.assertIn("cues[0].at", result.stderr)
        self.assertFalse((self.root / "stem.wav").exists())

        cue["at"] = 0
        cue["fade_out_ms"] = 20
        result = self.run_render({"version": 1, "cues": [cue]})
        self.assertEqual(result.returncode, 2)
        self.assertIn("fades exceed", result.stderr)
        self.assertFalse((self.root / "stem.wav").exists())

    def test_empty_cues_render_silence_when_duration_is_given(self) -> None:
        result = self.run_render({"version": 1, "duration_seconds": 0.04, "cues": []})
        self.assertEqual(result.returncode, 0, result.stderr)
        _, frames, left = read_wav(self.root / "stem.wav")
        self.assertEqual(frames, 1_920)
        self.assertEqual(max(abs(x) for x in left), 0)

    def test_overrun_requires_explicit_trim_and_reports_trimmed_samples(self) -> None:
        write_wav(self.root / "long.wav", [3_000] * 4_800)
        manifest = {
            "version": 1, "duration_seconds": 0.05,
            "cues": [{"id": "tail", "at": 0, "asset": "long.wav",
                      "gain_db": -12, "fade_in_ms": 0, "fade_out_ms": 0}],
        }
        rejected = self.run_render(manifest)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("overruns the timeline", rejected.stderr)
        self.assertFalse((self.root / "stem.wav").exists())

        allowed = self.run_render(manifest, "--trim-to-duration")
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        report = json.loads(allowed.stdout)
        self.assertEqual(report["placements"][0]["trimmed_samples"], 2_400)
        _, frames, _ = read_wav(self.root / "stem.wav")
        self.assertEqual(frames, 2_400)


if __name__ == "__main__":
    unittest.main()
