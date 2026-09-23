"""Focused behavior checks for the optional CapCut top/down recipe."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "capcut_video_assembler" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assembler = load_script("assemble_capcut_package")
split_template = load_script("top_down_split_template")


def test_srt_timestamps_round_across_second_boundary(tmp_path: Path):
    assert assembler.format_srt_timestamp(59.9996) == "00:01:00,000"
    assert assembler.format_srt_timestamp(3599.9996) == "01:00:00,000"
    with pytest.raises(ValueError):
        assembler.format_srt_timestamp(-1)

    srt = tmp_path / "captions.srt"
    assembler.generate_srt([{"start": 0, "end": 1.9996, "text": "A real caption"}], srt)
    assert "00:00:02,000" in srt.read_text()
    with pytest.raises(ValueError):
        assembler.generate_srt([{"start": 2, "end": 1, "text": "Backwards"}], srt)


def test_project_lookup_requires_exact_local_match(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(assembler.Path, "home", lambda: tmp_path)
    draft_root = tmp_path / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
    existing = draft_root / "existing-id"
    existing.mkdir(parents=True)
    (draft_root / "root_meta_info.json").write_text(json.dumps({
        "all_draft_store": [{
            "draft_name": "Existing Edit",
            "draft_fold_path": str(existing),
            "tm_draft_modified": 999,
        }]
    }))

    assert assembler.find_local_capcut_project() is None
    assert assembler.find_local_capcut_project("Missing Edit") is None
    assert assembler.find_local_capcut_project("Existing Edit") == existing
    with pytest.raises(ValueError, match="share URL"):
        assembler.find_local_capcut_project("https://www.capcut.com/view/123")


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg required")
def test_package_preserves_audio_format_and_does_not_write_to_draft(tmp_path: Path):
    top = tmp_path / "top.mp4"
    bottom = tmp_path / "bottom.mp4"
    voice = tmp_path / "voice.wav"
    for path, color, duration in ((top, "red", "1.2"), (bottom, "blue", "0.6")):
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=160x120:r=5",
            "-t", duration, "-c:v", "libx264", str(path),
        ], check=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "0.6", str(voice),
    ], check=True)

    draft = tmp_path / "existing-draft"
    draft.mkdir()
    (draft / "sentinel.txt").write_text("unchanged")
    output = tmp_path / "package"
    assembler.create_capcut_package(
        top, bottom, voice, output,
        render_master=False,
        capcut_project=str(draft),
    )

    assert sorted(p.name for p in draft.iterdir()) == ["sentinel.txt"]
    assert (output / "track3_voiceover.wav").read_bytes() == voice.read_bytes()
    assert assembler.probe_duration(output / "track1_top_story.mp4") == pytest.approx(0.6, abs=0.01)
    assert not (output / "captions.srt").exists()
    assert not (output / "master_preview_9x16.mp4").exists()
    guide = (output / "CAPCUT_QUICK_START.md").read_text()
    assert "track3_voiceover.wav" in guide
    assert "guard dog" not in guide.lower()


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg required")
def test_short_top_clip_fails_before_staging(tmp_path: Path):
    top = tmp_path / "short.mp4"
    voice = tmp_path / "voice.wav"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=red:s=160x120:r=10",
        "-t", "0.4", "-c:v", "libx264", str(top),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "0.6", str(voice),
    ], check=True)

    output = tmp_path / "package"
    with pytest.raises(ValueError, match="shorter than audio"):
        assembler.create_capcut_package(top, top, voice, output)
    assert not output.exists()

    preview = tmp_path / "short-preview.mp4"
    assert split_template.render_top_down_split(top, top, voice, preview) is False
    assert not preview.exists()


def test_cli_can_disable_preview_and_pass_caption_manifest(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "captions.json"
    manifest.write_text(json.dumps({"beats": [{"start": 0, "end": 1, "text": "My words"}]}))
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(assembler, "create_capcut_package", fake_create)
    monkeypatch.setattr(sys, "argv", [
        "assemble_capcut_package.py", "--top-video", "top.mp4",
        "--bottom-video", "bottom.mp4", "--audio", "voice.wav",
        "--transcript-json", str(manifest), "--no-render-master",
    ])
    assembler.main()
    assert captured["render_master"] is False
    assert captured["capcut_project"] is None
    assert captured["beats"] == [{"start": 0, "end": 1, "text": "My words"}]
    assert captured["manifest_path"] == manifest

    captured.clear()
    monkeypatch.setattr(sys, "argv", [
        "assemble_capcut_package.py", "--top-video", "top.mp4",
        "--bottom-video", "bottom.mp4", "--audio", "voice.wav",
    ])
    assembler.main()
    assert captured["render_master"] is False


def test_split_preview_uses_supplied_manifest_without_default_text(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"beats": [{"start": 0, "end": 1, "text": "User text"}]}))
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(split_template, "render_top_down_split", fake_render)
    monkeypatch.setattr(sys, "argv", [
        "top_down_split_template.py", "--top-video", "top.mp4",
        "--bottom-video", "bottom.mp4", "--audio", "voice.wav",
        "--output", "preview.mp4", "--manifest", str(manifest),
    ])
    with pytest.raises(SystemExit) as result:
        split_template.main()
    assert result.value.code == 0
    assert captured["banners"] == []
    assert captured["captions"] == [{"start": 0, "end": 1, "text": "User text"}]

    captured.clear()
    monkeypatch.setattr(sys, "argv", [
        "top_down_split_template.py", "--top-video", "top.mp4",
        "--bottom-video", "bottom.mp4", "--audio", "voice.wav",
        "--output", "preview.mp4",
    ])
    with pytest.raises(SystemExit):
        split_template.main()
    assert captured["banners"] == []
    assert captured["captions"] == []
