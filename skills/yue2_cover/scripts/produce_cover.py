#!/usr/bin/env python3
"""End-to-end Cover Producer: Reference Audio + Lyrics -> New YuE2 Song.

Orchestrates:
1. Audio acquisition (download from URL if needed)
2. Transcription of vocal melody to ABC (via SheetSage2)
3. Chord stripping to obtain clean, chord-free melody ABC
4. Lyric syllable-to-note alignment audit
5. YuE2 generation with cot="melody" using local YuE2 models
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = SKILL_DIR.parent.parent


def find_yue_workspace(custom_path=None) -> Path:
    candidates = [
        custom_path,
        os.environ.get("YUE_WORKSPACE"),
        Path("/Users/malickdes/AIWORKSPACE/YuE-music"),
        WORKSPACE_DIR.parent / "YuE-music",
        WORKSPACE_DIR,
    ]
    for c in candidates:
        if c and Path(c).is_dir() and (Path(c) / "skills/yue2-music").is_dir():
            return Path(c).resolve()
    raise FileNotFoundError("Could not locate YuE-music workspace directory. Pass --yue-dir.")


def download_audio_if_url(source: str, output_dir: Path) -> Path:
    if source.startswith(("http://", "https://")):
        out_file = output_dir / "reference_audio.wav"
        print(f"[*] Downloading reference audio from URL via yt-dlp...")
        cmd = [
            "yt-dlp", "-x", "--audio-format", "wav",
            "-o", str(output_dir / "reference_audio.%(ext)s"),
            source
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            # Fallback to curl if yt-dlp fails (e.g. direct wav/mp3 link)
            print("[!] yt-dlp failed or not found, trying curl...")
            res2 = subprocess.run(["curl", "-s", "-L", "-o", str(out_file), source])
            if res2.returncode != 0 or not out_file.exists():
                raise RuntimeError(f"Failed to download audio: {res.stderr}")
        found = list(output_dir.glob("reference_audio.*"))
        if not found:
            raise FileNotFoundError("Downloaded audio file not found.")
        return found[0]
    p = Path(source).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Audio file not found: {source}")
    return p


def convert_to_wav(flac_path: Path, wav_path: Path) -> bool:
    """Convert generated audio to standard 24-bit 48kHz WAV format."""
    try:
        import soundfile as sf
        data, sr = sf.read(str(flac_path))
        sf.write(str(wav_path), data, sr, subtype="PCM_24")
        return True
    except Exception:
        pass

    cmd = ["ffmpeg", "-y", "-i", str(flac_path), "-c:a", "pcm_s24le", str(wav_path)]
    res = subprocess.run(cmd, capture_output=True)
    return res.returncode == 0 and wav_path.is_file()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", help="Path to reference audio file or URL")
    parser.add_argument("--abc-file", type=Path, help="Existing clean ABC file (skips transcription)")
    parser.add_argument("--lyrics", required=True, help="Path to lyrics file (.txt/.json) or raw lyrics string")
    parser.add_argument("--style", required=True, help="Target music style, instruments, vocals, BPM")
    parser.add_argument("--output", required=True, type=Path, help="Destination directory for output artifacts")
    parser.add_argument("--id", default="cover_song", help="Unique song ID")
    parser.add_argument("--seed", type=int, default=831001, help="Random seed")
    parser.add_argument("--device", default="mps", help="Inference device: mps, cuda, or cpu")
    parser.add_argument("--yue-dir", type=Path, help="Path to YuE-music workspace root")
    parser.add_argument("--skip-generation", action="store_true", help="Stop after ABC prep & lyric audit")
    args = parser.parse_args()

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    yue_root = find_yue_workspace(args.yue_dir)
    print(f"[*] YuE-music workspace located at: {yue_root}")

    # 1. Resolve lyrics text/file
    lyrics_text = ""
    lyrics_path = Path(args.lyrics)
    if lyrics_path.is_file():
        lyrics_text = lyrics_path.read_text(encoding="utf-8")
        try:
            data = json.loads(lyrics_text)
            if isinstance(data, dict) and "lyrics" in data:
                lyrics_text = data["lyrics"]
        except Exception:
            pass
    else:
        lyrics_text = args.lyrics

    (out / "lyrics.txt").write_text(lyrics_text, encoding="utf-8")

    # 2. Get ABC Score
    clean_abc_path = out / "clean_melody.abc"
    if args.abc_file and args.abc_file.is_file():
        print(f"[*] Using provided ABC score: {args.abc_file}")
        shutil.copyfile(args.abc_file, clean_abc_path)
    else:
        if not args.audio:
            raise ValueError("Must provide either --audio or --abc-file")
        audio_file = download_audio_if_url(args.audio, out)
        print(f"[*] Reference audio: {audio_file}")

        # Transcribe
        transcribe_script = yue_root / "skills/yue2-music/scripts/transcribe.py"
        transcribe_out = out / "transcription"
        print(f"[*] Transcribing vocal melody with SheetSage2...")
        cmd_transcribe = [
            sys.executable, str(transcribe_script),
            str(audio_file),
            "--task", "melody-vocal",
            "--output", str(transcribe_out)
        ]
        res = subprocess.run(cmd_transcribe, capture_output=True, text=True)
        raw_abc = transcribe_out / "score.abc"
        if not raw_abc.is_file():
            print(f"[!] Transcription output:\n{res.stdout}\n{res.stderr}")
            raise RuntimeError(f"Transcription failed to produce {raw_abc}")

        # Strip chords
        print(f"[*] Stripping chords to isolate pure vocal melody...")
        abc_tools = SKILL_DIR / "scripts/abc_tools.py"
        cmd_strip = [
            sys.executable, str(abc_tools), "strip-chords",
            str(raw_abc), str(clean_abc_path),
            "--keep-voice", "Vocal"
        ]
        res_strip = subprocess.run(cmd_strip, capture_output=True, text=True)
        if res_strip.returncode != 0 or not clean_abc_path.is_file():
            raise RuntimeError(f"Failed to strip chords: {res_strip.stderr}")

    # 3. Lyric-to-melody Syllable Audit
    print(f"[*] Auditing lyric syllables against melody notes...")
    align_script = SKILL_DIR / "scripts/align_lyrics.py"
    audit_cmd = [sys.executable, str(align_script), str(clean_abc_path), str(out / "lyrics.txt")]
    subprocess.run(audit_cmd)

    if args.skip_generation:
        print("[*] --skip-generation enabled. Completed prep stage.")
        return 0

    # 4. Prepare Request JSON
    req_data = {
        "id": args.id,
        "style": args.style,
        "lyrics": lyrics_text,
        "cot": "melody",
        "seed": args.seed
    }
    req_file = out / "request.json"
    req_file.write_text(json.dumps(req_data, indent=2), encoding="utf-8")
    print(f"[*] Prepared {req_file}")

    # 5. Run YuE2 Generation
    gen_script = yue_root / "skills/yue2-music/scripts/run_yue2.py"
    model_dir = yue_root / "models/YuE2-3B"
    vae_dir = yue_root / "models/YuE2-Vae"
    gen_out = out / "song"

    py_exec = sys.executable
    if (yue_root / ".venv/bin/python").is_file():
        py_exec = str(yue_root / ".venv/bin/python")

    print(f"[*] Launching YuE2 generation on device: {args.device}...")
    cmd_gen = [
        py_exec, str(gen_script), "generate",
        "--request", str(req_file),
        "--abc-file", str(clean_abc_path),
        "--cot", "melody",
        "--output", str(gen_out),
        "--model", str(model_dir),
        "--vae", str(vae_dir),
        "--offline",
        "--device", args.device
    ]
    print(f"    Command: {' '.join(cmd_gen)}")
    res_gen = subprocess.run(cmd_gen)
    if res_gen.returncode != 0:
        print(f"[!] Generation exited with code {res_gen.returncode}")
        return res_gen.returncode

    print(f"\n[✓] Song generation complete!")
    flac_file = gen_out / "audio.flac"
    final_wav = out / f"{args.id}.wav"
    gen_wav = gen_out / "audio.wav"

    if flac_file.is_file():
        print(f"[*] Converting output to final WAV: {final_wav.name}...")
        if convert_to_wav(flac_file, final_wav):
            shutil.copyfile(final_wav, gen_wav)
            print(f"\n[✓] Final WAV Output ready:")
            print(f"    ▶ {final_wav}")
        else:
            print(f"[!] FLAC available at: {flac_file} (WAV conversion failed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
