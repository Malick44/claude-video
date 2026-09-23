#!/usr/bin/env python3
"""AuK Voiceover Generator: Zero-shot Voice Cloning from Transcripts.

Synthesize high-fidelity voiceover speech given a text transcript and a reference audio sample,
using the local AuK-Voice foundation speech model (MLX on Apple Silicon).

Usage:
    python3 generate_voiceover.py --transcript "Hello world" --ref-audio /path/to/ref.wav -o output.wav
    python3 generate_voiceover.py --transcript transcript.json -o voiceover.wav
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

DEFAULT_AUK_ROOT = "/Users/malickdes/AIWORKSPACE/AuK-Voice"
DEFAULT_REF_VOICE = (
    "/Users/malickdes/AIWORKSPACE/AuK-Voice/assets/us-female/"
    "inworld-tts-2-flash_Zadie_English_09-18-2026 11-09-11.wav"
)


class AudioChunk(TypedDict, total=False):
    id: str
    text: str
    duration: float
    banner: str
    tone: str | None


def ensure_macosapps_mounted(auk_root: str = DEFAULT_AUK_ROOT) -> bool:
    """Ensure required AuK checkpoints and configs are available locally or on MacosApps."""
    local_cfg = Path(auk_root) / "ckpts" / "AuK-Flash" / "config.yaml"
    local_mlx = Path(auk_root) / "ckpts" / "mlx" / "dit_flash.safetensors"
    if local_cfg.is_file() and local_mlx.is_file():
        return True

    macosapps_path = Path("/Volumes/MacosApps")
    if macosapps_path.exists() and (macosapps_path / "AuK-Voice").exists():
        return True

    # Try mounting disk18s3 or finding MacosApps
    try:
        res = subprocess.run(
            ["diskutil", "mount", "disk18s3"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if res.returncode == 0 and macosapps_path.exists():
            print("[auk_voiceover] Successfully mounted /Volumes/MacosApps (disk18s3)", file=sys.stderr)
            return True
    except (subprocess.SubprocessError, OSError):
        pass

    # Search for MacosApps identifier in diskutil list
    try:
        proc = subprocess.run(
            ["diskutil", "list"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        for line in proc.stdout.splitlines():
            if "MacosApps" in line:
                parts = line.split()
                ident = parts[-1]
                subprocess.run(
                    ["diskutil", "mount", ident],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if macosapps_path.exists():
                    return True
    except (subprocess.SubprocessError, OSError):
        pass

    return macosapps_path.exists()


def check_and_trampoline_env(auk_root: str) -> None:
    """If current python environment does not have auk_mlx, re-exec with AuK uv/venv."""
    try:
        import auk_mlx  # type: ignore[import-not-found] # noqa: F401
        import mlx.core  # type: ignore[import-not-found] # noqa: F401
        import soundfile  # type: ignore[import-not-found] # noqa: F401
    except ImportError:
        # Re-invoke under AuK-Voice uv run or .venv
        auk_venv_py = os.path.join(auk_root, ".venv", "bin", "python")
        cmd = []
        if os.path.isfile(auk_venv_py) and os.access(auk_venv_py, os.X_OK):
            env = os.environ.copy()
            src_dir = os.path.join(auk_root, "src")
            env["PYTHONPATH"] = f"{src_dir}:{env.get('PYTHONPATH', '')}".rstrip(":")
            cmd = [auk_venv_py, os.path.abspath(__file__)] + sys.argv[1:]
            os.execve(auk_venv_py, cmd, env)
        else:
            # Fallback to uv run
            env = os.environ.copy()
            src_dir = os.path.join(auk_root, "src")
            env["PYTHONPATH"] = f"{src_dir}:{env.get('PYTHONPATH', '')}".rstrip(":")
            cmd = ["uv", "run", "--project", auk_root, "python", os.path.abspath(__file__)] + sys.argv[1:]
            os.execvpe("uv", cmd, env)


def parse_transcript_input(
    transcript_arg: str,
    target_duration: float | None = None,
    wpm: float = 172.0,
) -> list[AudioChunk]:
    """Parse transcript string or file into an ordered list of generation chunks.
    
    Each chunk dict has:
      - 'id': str
      - 'text': str
      - 'duration': float (target generation seconds)
      - 'banner': str (optional banner headline)
      - 'tone': str | None (optional vocal delivery cue)
    """
    chunks: list[AudioChunk] = []
    path = Path(transcript_arg)

    if path.is_file():
        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data: Any = json.load(f)

            if "beats" in data and isinstance(data["beats"], list):
                # Structured transcript from dylan_hook_voiceover
                for i, beat in enumerate(data["beats"]):
                    text = str(beat.get("text", "")).strip()
                    if not text:
                        continue
                    dur = float(beat.get("duration", 0.0))
                    if dur <= 0:
                        words = len(text.split())
                        dur = max(2.0, (words / wpm) * 60.0)
                    
                    beat_tone = beat.get("tone")
                    if not beat_tone and beat.get("inflection"):
                        # Extract first vocal cue from inflection string e.g. "[Intense Whisper / ...]"
                        clean_inf = re.sub(r"[\[\]]", "", str(beat["inflection"])).split("/")[0].strip().lower()
                        if clean_inf:
                            beat_tone = clean_inf

                    chunks.append({
                        "id": str(beat.get("beat_id", f"beat_{i+1:02d}")),
                        "text": text,
                        "duration": round(dur, 2),
                        "banner": str(beat.get("banner_headline", "")),
                        "tone": beat_tone,
                    })
                return chunks
            elif "text" in data:
                raw_text = data["text"]
            else:
                raw_text = json.dumps(data)
        else:
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()
    else:
        raw_text = transcript_arg

    # Clean raw text from markdown / timestamps / annotations
    clean_lines = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "---")):
            continue
        # Remove bracketed cues like [Intense Whisper]
        line = re.sub(r"\[.*?\]", "", line).strip()
        if line:
            clean_lines.append(line)

    full_text = " ".join(clean_lines)
    full_words = full_text.split()
    total_words = len(full_words)

    # If short text, return as single chunk
    if total_words <= 50 and (target_duration is None or target_duration <= 22.0):
        dur = target_duration if target_duration else max(2.5, (total_words / wpm) * 60.0)
        return [{"id": "chunk_01", "text": full_text, "duration": round(dur, 2), "banner": "", "tone": None}]

    # Sentence-based chunking for longer scripts
    sentences = re.split(r"(?<=[.!?])\s+", full_text)
    current_chunk_words: list[str] = []
    chunk_idx = 1

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        s_words = s.split()
        if len(current_chunk_words) + len(s_words) > 35 and current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            c_words = len(current_chunk_words)
            c_dur = max(2.5, (c_words / wpm) * 60.0)
            chunks.append({
                "id": f"chunk_{chunk_idx:02d}",
                "text": chunk_text,
                "duration": round(c_dur, 2),
                "banner": "",
                "tone": None,
            })
            chunk_idx += 1
            current_chunk_words = list(s_words)
        else:
            current_chunk_words.extend(s_words)

    if current_chunk_words:
        chunk_text = " ".join(current_chunk_words)
        c_words = len(current_chunk_words)
        c_dur = max(2.5, (c_words / wpm) * 60.0)
        chunks.append({
            "id": f"chunk_{chunk_idx:02d}",
            "text": chunk_text,
            "duration": round(c_dur, 2),
            "banner": "",
            "tone": None,
        })

    # If target_duration is given, proportionally scale chunk durations
    if target_duration is not None and chunks:
        current_total = sum(c.get("duration", 0.0) for c in chunks)
        if current_total > 0:
            scale = target_duration / current_total
            for c in chunks:
                c["duration"] = round(c.get("duration", 0.0) * scale, 2)

    return chunks


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate high-fidelity cloned voiceover audio from a transcript using local AuK-Voice MLX."
    )
    p.add_argument(
        "--transcript", "-t",
        required=True,
        help="Spoken transcript text, or path to .txt / transcript.json file.",
    )
    p.add_argument(
        "--ref-audio", "-r",
        default=DEFAULT_REF_VOICE,
        help=f"Path to reference audio file (.wav, .mp3). Default: {DEFAULT_REF_VOICE}",
    )
    p.add_argument(
        "--output", "-o",
        default="outputs/voiceover.wav",
        help="Destination audio path (.wav). Default: outputs/voiceover.wav",
    )
    p.add_argument(
        "--duration", "-d",
        type=float,
        default=None,
        help="Total target duration in seconds. If omitted, computed automatically from WPM cadence.",
    )
    p.add_argument(
        "--wpm",
        type=float,
        default=172.0,
        help="Words per minute speaking rate (default: 172.0 for viral short-form cadence).",
    )
    p.add_argument(
        "--engine",
        choices=["flash", "base"],
        default="flash",
        help="AuK model engine: 'flash' (4-step fast distilled) or 'base' (32-step ODE). Default: flash.",
    )
    p.add_argument(
        "--pause",
        type=float,
        default=0.15,
        help="Micro-pause between chunks in seconds (default: 0.15s).",
    )
    p.add_argument(
        "--tone",
        default=None,
        help="Vocal tone/emotion instruction (e.g. 'energetic', 'excited', 'intense', 'dramatic').",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible generation (default: 42).",
    )
    p.add_argument(
        "--auk-root",
        default=DEFAULT_AUK_ROOT,
        help=f"Path to AuK-Voice repository (default: {DEFAULT_AUK_ROOT}).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output structured metadata JSON to stdout upon completion.",
    )

    args = p.parse_args()

    # 1. Mount external checkpoints if needed
    if not ensure_macosapps_mounted(args.auk_root):
        print("[auk_voiceover] Warning: AuK checkpoints not found locally or on /Volumes/MacosApps.", file=sys.stderr)

    # 2. Check environment and trampoline if necessary
    check_and_trampoline_env(args.auk_root)

    # Now imports are guaranteed
    import numpy as np  # type: ignore[import-not-found]
    import soundfile as sf  # type: ignore[import-not-found]
    from auk_mlx.infer import AukMLX, GenerateOptions  # type: ignore[import-not-found]

    ref_path = os.path.abspath(args.ref_audio)
    if not os.path.isfile(ref_path):
        raise FileNotFoundError(f"Reference voice audio file not found: {ref_path}")

    # 3. Parse transcript into generation chunks
    chunks = parse_transcript_input(args.transcript, target_duration=args.duration, wpm=args.wpm)
    if not chunks:
        raise ValueError("No speakable text found in the provided transcript.")

    print(f"\n[auk_voiceover] 🎙️ Initializing AuK-Voice ({args.engine})...")
    print(f"[auk_voiceover] Reference voice: {ref_path}")
    print(f"[auk_voiceover] Total chunks: {len(chunks)} | Target WPM: {args.wpm:.1f}")

    # 4. Initialize MLX Engine
    cfg_file = "config.yaml"
    ckpt_dir_name = "AuK-Flash" if args.engine == "flash" else "AuK"
    config_path = os.path.join(args.auk_root, "ckpts", ckpt_dir_name, cfg_file)
    mlx_dir = os.path.join(args.auk_root, "ckpts", "mlx")
    qwen_dir = os.path.join(args.auk_root, "ckpts", "Qwen2.5-Omni-3B")

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Missing config at {config_path}. Ensure external drive MacosApps is mounted.")

    eng = AukMLX(mlx_dir, config_path, qwen_dir)
    print("[auk_voiceover] Model loaded successfully into Apple Silicon unified memory.\n")

    # 5. Generate audio chunk-by-chunk
    generated_wavs = []
    chunk_metadata = []
    sample_rate = 24000
    current_time_offset = 0.0

    pause_samples = int(max(0.0, args.pause) * sample_rate)
    pause_silence = np.zeros(pause_samples, dtype=np.float32)

    for idx, c in enumerate(chunks, 1):
        cid: str = str(c.get("id", f"chunk_{idx:02d}"))
        text: str = str(c.get("text", ""))
        target_dur: float = float(c.get("duration", 3.0))

        clean_text = text.replace('"', '').strip()
        chunk_tone: str | None = c.get("tone") or args.tone

        if chunk_tone:
            instruction = f'Say the following in the same voice with an {chunk_tone} delivery: "{clean_text}"'
        else:
            instruction = f'Say the following with the same voice: "{clean_text}"'

        tone_str = f" | tone: '{chunk_tone}'" if chunk_tone else ""
        print(f"[{idx}/{len(chunks)}] Synthesizing '{cid}' ({target_dur:.1f}s, {len(text.split())} words{tone_str})...")
        print(f"       Text: \"{text[:75]}{'...' if len(text) > 75 else ''}\"")

        opts = GenerateOptions(gen_seconds=target_dur, seed=args.seed + idx)
        if args.engine == "base":
            opts.nfe = 32

        chunk_wav, sr = eng.generate(instruction, audio_path=ref_path, opts=opts)
        sample_rate = sr

        actual_chunk_dur = len(chunk_wav) / sr
        chunk_metadata.append({
            "chunk_id": cid,
            "text": text,
            "start_time": round(current_time_offset, 3),
            "end_time": round(current_time_offset + actual_chunk_dur, 3),
            "duration": round(actual_chunk_dur, 3),
            "banner": c.get("banner", ""),
        })
        current_time_offset += actual_chunk_dur + (args.pause if idx < len(chunks) else 0.0)

        generated_wavs.append(chunk_wav)
        if idx < len(chunks) and pause_samples > 0:
            generated_wavs.append(pause_silence)

    # 6. Stitch together and normalize
    full_audio = np.concatenate(generated_wavs)
    peak = float(np.abs(full_audio).max())
    if peak > 0:
        # Standard broadcast peak normalization to -0.8 dBFS (~0.91)
        full_audio = (full_audio / peak) * 0.91
        rms = float(np.sqrt((full_audio**2).mean()))
    else:
        rms = 0.0

    total_dur = len(full_audio) / sample_rate

    # 7. Write output file
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), full_audio, sample_rate)

    print("\n[auk_voiceover] ✅ Voiceover synthesis complete!")
    print(f"[auk_voiceover] Output file:   {out_path}")
    print(f"[auk_voiceover] Total duration: {total_dur:.2f}s ({len(chunks)} chunks)")
    print(f"[auk_voiceover] Sample rate:   {sample_rate} Hz (mono)")
    print(f"[auk_voiceover] Peak amplitude: {np.abs(full_audio).max():.3f} | RMS: {rms:.4f}")

    if args.json:
        result_payload = {
            "status": "success",
            "audio_file": str(out_path),
            "total_duration": round(total_dur, 3),
            "sample_rate": sample_rate,
            "engine": args.engine,
            "ref_audio": ref_path,
            "chunks": chunk_metadata,
        }
        print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
    main()
