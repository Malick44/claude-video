#!/usr/bin/env python3
"""Place resolved sound cues on a sample-accurate 48 kHz timeline with FFmpeg.

The input is a reviewed cue manifest, not an instruction to infer sound design:

    {"version": 1, "duration_seconds": 8.0, "cues": [
      {"id": "reveal", "at": 3.125, "asset": "sounds/impact.wav",
       "gain_db": -18, "fade_in_ms": 0, "fade_out_ms": 120}
    ]}

Relative asset paths resolve from the manifest's directory. Extra descriptive cue
fields (for example reason and tension_before) are retained in the input but do
not change rendering. A cue that overruns an explicit timeline duration is
rejected unless --trim-to-duration is supplied; the report then records the
number of samples trimmed. The standalone stem is stereo 32-bit float PCM WAV
so overlapping cues keep headroom; the optional limited preview mix is PCM16.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


SAMPLE_RATE = 48_000
MAX_CUES = 256
MAX_SECONDS = 4 * 60 * 60


@dataclass(frozen=True)
class Cue:
    id: str
    at_samples: int
    asset: Path
    asset_samples: int
    channels: int
    gain_db: float
    fade_in_samples: int
    fade_out_samples: int
    metadata: dict[str, object]


def _number(value: object, label: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result) or result < lo or result > hi:
        raise ValueError(f"{label} must be finite and between {lo} and {hi}")
    return result


def _samples(seconds: float) -> int:
    return round(seconds * SAMPLE_RATE)


def probe_audio_info(path: Path) -> tuple[float, int]:
    """Return decoded audio duration and channels, independent of video length."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=channels,sample_rate", "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode:
        raise ValueError(f"ffprobe failed for {path}: {proc.stderr.strip()}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"ffprobe returned invalid JSON for {path}") from exc
    streams = data.get("streams") or []
    if not streams:
        raise ValueError(f"No audio stream in {path}")
    try:
        sample_rate = int(streams[0].get("sample_rate"))
        channels = int(streams[0].get("channels"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Audio format unavailable for {path}") from exc
    if sample_rate <= 0 or channels <= 0:
        raise ValueError(f"Audio format invalid for {path}")

    # Some containers report their video length as format.duration while the
    # audio stream has no duration field. Sum decoded audio-frame samples so a
    # short sound in a longer video container cannot lengthen the cue timeline.
    command = [
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_frames",
        "-show_entries", "frame=nb_samples", "-of", "csv=p=0", str(path),
    ]
    frame_probe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
    decoded_samples = 0
    assert frame_probe.stdout is not None
    for line in frame_probe.stdout:
        token = line.strip().split(",", 1)[0]
        if token.isdecimal():
            decoded_samples += int(token)
    stderr = frame_probe.stderr.read() if frame_probe.stderr else ""
    if frame_probe.wait():
        raise ValueError(f"Audio frame probe failed for {path}: {stderr.strip()}")
    duration = decoded_samples / sample_rate
    if duration <= 0 or duration > MAX_SECONDS:
        raise ValueError(f"Decoded audio duration out of range for {path}")
    return duration, channels


def _stereo_filter(channels: int) -> str:
    """Duplicate mono at unity gain; retain the existing stereo channel levels."""
    base = "aformat=sample_fmts=fltp:channel_layouts=stereo"
    return f"pan=stereo|c0=c0|c1=c0,{base}" if channels == 1 else base


def load_manifest(path: Path) -> tuple[list[Cue], float | None]:
    """Validate cue fields and resolve all assets without modifying the manifest."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read cue JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("Cue JSON must be an object with version: 1")
    raw_cues = data.get("cues")
    if not isinstance(raw_cues, list) or len(raw_cues) > MAX_CUES:
        raise ValueError(f"cues must be an array of at most {MAX_CUES} items")
    duration = data.get("duration_seconds")
    if duration is not None:
        duration = _number(duration, "duration_seconds", 1 / SAMPLE_RATE, MAX_SECONDS)

    cues: list[Cue] = []
    ids: set[str] = set()
    info_cache: dict[Path, tuple[float, int]] = {}
    for index, raw in enumerate(raw_cues):
        label = f"cues[{index}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{label} must be an object")
        cue_id = raw.get("id")
        if not isinstance(cue_id, str) or not cue_id.strip() or cue_id in ids:
            raise ValueError(f"{label}.id must be a unique nonempty string")
        ids.add(cue_id)
        at = _number(raw.get("at"), f"{label}.at", 0, MAX_SECONDS)
        gain = _number(raw.get("gain_db"), f"{label}.gain_db", -90, 12)
        fade_in = _number(raw.get("fade_in_ms"), f"{label}.fade_in_ms", 0, MAX_SECONDS * 1000)
        fade_out = _number(raw.get("fade_out_ms"), f"{label}.fade_out_ms", 0, MAX_SECONDS * 1000)
        asset_text = raw.get("asset")
        if not isinstance(asset_text, str) or not asset_text.strip():
            raise ValueError(f"{label}.asset must be a nonempty path")
        asset = Path(asset_text).expanduser()
        if not asset.is_absolute():
            asset = path.parent / asset
        asset = asset.resolve()
        if not asset.is_file():
            raise ValueError(f"{label}.asset does not exist: {asset}")
        if asset not in info_cache:
            info_cache[asset] = probe_audio_info(asset)
        asset_duration, asset_channels = info_cache[asset]
        asset_samples = _samples(asset_duration)
        if asset_samples <= 0:
            raise ValueError(f"{label}.asset is shorter than one output sample")
        cues.append(Cue(
            id=cue_id,
            at_samples=_samples(at),
            asset=asset,
            asset_samples=asset_samples,
            channels=asset_channels,
            gain_db=gain,
            fade_in_samples=_samples(fade_in / 1000),
            fade_out_samples=_samples(fade_out / 1000),
            metadata={key: raw[key] for key in ("reason", "tension_before", "tension_after")
                      if key in raw},
        ))
    return cues, duration


def _run_ffmpeg(inputs: list[Path], graph: str, output_label: str, target: Path,
                codec: str) -> None:
    """Render into a temporary WAV and replace the destination only on success."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cinematic-sfx-") as temp_dir:
        graph_file = Path(temp_dir) / "filter.graph"
        graph_file.write_text(graph, encoding="utf-8")
        staged = Path(temp_dir) / "render.wav"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
        for source in inputs:
            command += ["-i", str(source)]
        command += [
            "-filter_complex_script", str(graph_file), "-map", f"[{output_label}]",
            "-ar", str(SAMPLE_RATE), "-ac", "2", "-c:a", codec, str(staged),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode:
            raise RuntimeError(f"FFmpeg render failed: {proc.stderr.strip()}")
        # Preserve the destination if rendering failed; avoid cross-volume rename.
        with tempfile.NamedTemporaryFile(
            prefix=f".{target.stem}-", suffix=".wav", dir=target.parent, delete=False
        ) as handle:
            temporary_target = Path(handle.name)
        try:
            shutil.copyfile(staged, temporary_target)
            os.replace(temporary_target, target)
        finally:
            temporary_target.unlink(missing_ok=True)


def render_stem(cues: list[Cue], total_samples: int, target: Path,
                trim_to_duration: bool = False) -> None:
    """Mix cues over a silent base, positioning each at an integer sample index."""
    graph = [
        f"anullsrc=channel_layout=stereo:sample_rate={SAMPLE_RATE},"
        f"atrim=end_sample={total_samples},asetpts=PTS-STARTPTS[base]"
    ]
    labels = ["[base]"]
    for index, cue in enumerate(cues):
        available = total_samples - cue.at_samples
        if available <= 0:
            raise ValueError(f"Cue {cue.id} starts at or after the timeline end")
        if cue.asset_samples > available and not trim_to_duration:
            raise ValueError(
                f"Cue {cue.id} overruns the timeline by "
                f"{(cue.asset_samples - available) / SAMPLE_RATE:.3f}s; "
                "use --trim-to-duration to trim deliberately"
            )
        clip_samples = min(cue.asset_samples, available)
        if cue.fade_in_samples + cue.fade_out_samples > clip_samples:
            raise ValueError(f"Cue {cue.id} fades exceed its available {clip_samples / SAMPLE_RATE:.3f}s")
        parts = [
            f"[{index}:a:0]aresample={SAMPLE_RATE}",
            _stereo_filter(cue.channels),
            f"atrim=end_sample={clip_samples}",
            "asetpts=PTS-STARTPTS",
        ]
        if cue.fade_in_samples:
            parts.append(f"afade=t=in:ss=0:ns={cue.fade_in_samples}")
        if cue.fade_out_samples:
            start = clip_samples - cue.fade_out_samples
            parts.append(f"afade=t=out:ss={start}:ns={cue.fade_out_samples}")
        parts += [
            f"volume={cue.gain_db:.6f}dB",
            f"adelay={cue.at_samples}S:all=1",
        ]
        graph.append(",".join(parts) + f"[cue{index}]")
        labels.append(f"[cue{index}]")
    if cues:
        graph.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=first:dropout_transition=0:normalize=0,"
            + f"atrim=end_sample={total_samples}[sfx]"
        )
    else:
        graph.append("[base]anull[sfx]")
    _run_ffmpeg([cue.asset for cue in cues], ";\n".join(graph), "sfx", target,
                "pcm_f32le")


def render_mix(narration: Path, stem: Path, total_samples: int, target: Path,
               narration_channels: int) -> None:
    """Duck the SFX under speech, then peak-limit the optional preview mix."""
    graph = ";\n".join([
        f"[0:a:0]aresample={SAMPLE_RATE},{_stereo_filter(narration_channels)},"
        f"apad,atrim=end_sample={total_samples},asetpts=PTS-STARTPTS,asplit=2[voice][sidechain]",
        f"[1:a:0]aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"atrim=end_sample={total_samples},asetpts=PTS-STARTPTS[effects]",
        "[effects][sidechain]sidechaincompress=threshold=0.06:ratio=4:attack=20:release=220[ducked]",
        f"[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        f"alimiter=limit=0.891251:level=false:latency=true,atrim=end_sample={total_samples}[mixed]",
    ])
    _run_ffmpeg([narration, stem], graph, "mixed", target, "pcm_s16le")


def stem_peak_dbfs(stem: Path) -> float | None:
    """Measure the float stem peak, including values above digital full scale."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(stem),
         "-af", "astats=metadata=0:reset=0", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode:
        raise RuntimeError(f"Stem peak measurement failed: {proc.stderr.strip()}")
    peaks = re.findall(r"Peak level dB:\s*([^\s]+)", proc.stderr)
    if not peaks:
        raise RuntimeError("Stem peak measurement returned no peak level")
    peak = float(peaks[-1])  # astats prints channel results, then Overall last.
    return peak if math.isfinite(peak) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cues", required=True, type=Path, help="Resolved cue JSON")
    parser.add_argument("--stem", required=True, type=Path, help="Standalone SFX stem (.wav)")
    parser.add_argument("--narration", type=Path, help="Narration audio for an optional preview mix")
    parser.add_argument("--mix", type=Path, help="Optional narration plus SFX preview (.wav)")
    parser.add_argument("--duration", type=float, help="Override the manifest timeline duration in seconds")
    parser.add_argument("--trim-to-duration", action="store_true",
                        help="Intentionally trim any effect tail that overruns an explicit duration")
    args = parser.parse_args(argv)
    if (args.narration is None) != (args.mix is None):
        parser.error("--narration and --mix must be provided together")
    if args.stem.suffix.lower() != ".wav" or (args.mix and args.mix.suffix.lower() != ".wav"):
        parser.error("--stem and --mix must have .wav extensions")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        parser.error("ffmpeg and ffprobe are required")

    try:
        manifest = args.cues.expanduser().resolve()
        cues, declared_duration = load_manifest(manifest)
        narration = args.narration.expanduser().resolve() if args.narration else None
        narration_info = probe_audio_info(narration) if narration else None
        narration_duration = narration_info[0] if narration_info else None
        if args.duration is not None:
            total_seconds = _number(args.duration, "--duration", 1 / SAMPLE_RATE, MAX_SECONDS)
        elif declared_duration is not None:
            total_seconds = declared_duration
        else:
            total_seconds = max(
                [cue.at_samples / SAMPLE_RATE + cue.asset_samples / SAMPLE_RATE for cue in cues]
                + ([narration_duration] if narration_duration is not None else [0])
            )
        total_samples = _samples(total_seconds)
        if total_samples <= 0 or total_samples > MAX_SECONDS * SAMPLE_RATE:
            raise ValueError("Timeline must be between one sample and four hours")
        protected = {manifest, *(cue.asset for cue in cues)}
        if narration:
            protected.add(narration)
        stem = args.stem.expanduser().resolve()
        mix = args.mix.expanduser().resolve() if args.mix else None
        if stem in protected or (mix and (mix in protected or mix == stem)):
            raise ValueError("Output paths must differ from inputs and each other")

        render_stem(cues, total_samples, stem, args.trim_to_duration)
        peak_dbfs = stem_peak_dbfs(stem)
        if narration and mix:
            render_mix(narration, stem, total_samples, mix, narration_info[1])
        print(json.dumps({
            "stem": str(stem), "mix": str(mix) if mix else None,
            "duration_seconds": total_samples / SAMPLE_RATE,
            "sample_rate": SAMPLE_RATE,
            "stem_peak_dbfs": peak_dbfs,
            "stem_headroom_db": -peak_dbfs if peak_dbfs is not None else None,
            "placements": [{
                "id": cue.id,
                "at_sample": cue.at_samples,
                "at_seconds": cue.at_samples / SAMPLE_RATE,
                "trimmed_samples": max(0, cue.asset_samples - (total_samples - cue.at_samples)),
                **cue.metadata,
            } for cue in cues],
        }, indent=2))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"render_cues: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
