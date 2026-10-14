"""Make an upload copy of the rendered episode under a size cap (two-pass H.264).

  python pipeline/deliver.py episodes/<episode> [--max-mb 29] [--allow-draft]

Reads build/<episode>.mp4, writes build/<episode>_tiktok.mp4. The master render
carries heavy film grain (~9 Mbps); TikTok re-encodes to a similar bitrate as
this copy anyway, and it fits under chat/email attachment limits.

It refuses an episode whose reenactment plays a Blender clip (blender_reenact.py) rendered with a PROXY
model or below --quality final, as build/timeline.json records it ("clip_blender"): a proxy is a
placeholder, never a deliverable. --allow-draft makes the copy anyway (a test upload), with a warning.
"""
import json
import os
import subprocess
import sys

from common import load_episode


def drafts(ep):
    """The reenactments playing a Blender clip that isn't deliverable: [(shot id, clip, why)]."""
    path = os.path.join(ep.BUILD, "timeline.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        shots = json.load(f)["shots"]
    out = []
    for s in shots:
        b = s.get("clip_blender")
        if b and (b.get("proxy") or b.get("quality") != "final"):
            why = ", ".join(x for x in ("a PROXY model" if b.get("proxy") else "",
                                        f"quality {b.get('quality')}" if b.get("quality") != "final" else "") if x)
            out.append((s["id"], s["clip"], why))
    return out


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        sys.exit("usage: deliver.py episodes/<episode> [--max-mb 29]")
    ep = load_episode(args[0])
    bad = drafts(ep)
    for sid, clip, why in bad:
        print(f"{'WARN' if '--allow-draft' in args else 'ERROR'} shot {sid}: Blender clip {clip} has {why}; "
              f"render it with pipeline/blender_reenact.py {args[0]} --quality final --require-models "
              "(docs/BLENDER_REENACTMENTS.md, \"Rendering finals on a GPU machine\")", file=sys.stderr)
    if bad and "--allow-draft" not in args:
        sys.exit("not delivered: a proxy or draft reenactment is a placeholder (--allow-draft for a test upload)")
    max_mb = float(args[args.index("--max-mb") + 1]) if "--max-mb" in args else 29.0
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    src = os.path.join(ep.BUILD, f"{ep.SLUG}.mp4")
    dst = os.path.join(ep.BUILD, f"{ep.SLUG}_tiktok.mp4")
    probe = subprocess.run([ff, "-i", src], capture_output=True, text=True).stderr
    h, m, s = probe.split("Duration: ")[1].split(",")[0].split(":")
    dur = int(h) * 3600 + int(m) * 60 + float(s)
    audio_kbps = 128
    video_kbps = int(max_mb * 8 * 1024 * 0.97 / dur - audio_kbps)
    log = os.path.join(ep.BUILD, "pass")
    common = ["-vf", "hqdn3d=1.5:1.5:5:5", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-passlogfile", log]
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", src, *common, "-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", src, *common, "-pass", "2",
                    "-maxrate", f"{int(video_kbps * 1.3)}k", "-bufsize", f"{int(video_kbps * 2.6)}k",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-movflags", "+faststart", dst], check=True)
    for f in os.listdir(ep.BUILD):
        if f.startswith("pass"):
            os.remove(os.path.join(ep.BUILD, f))
    print(f"wrote {dst} ({os.path.getsize(dst) / 1e6:.1f} MB, {video_kbps} kbps video)")


if __name__ == "__main__":
    main()
