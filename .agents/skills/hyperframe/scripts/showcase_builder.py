#!/usr/bin/env python3
"""
showcase_builder.py — HyperFrames App Showcase & Phone Demo Video Generator
Supports:
  1. Fullscreen Phone Demo Mode (--demo-only / --fullscreen):
     Edge-to-edge 1080x1920 phone UI demo with zero titles, zero subtitles,
     cinematic UI pan/zoom, and MP4 rendering. (Ideal for modular pipelines
     where Higgsfield/characters are handled separately).
  2. 3D Device Showcase Mode:
     Full branded showcase with 3D device framing, kinetic typography, and callouts.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

NODE_PATH = "/Users/malickdes/.nvm/versions/node/v22.17.0/bin:/opt/homebrew/bin:/usr/local/bin"

def get_env():
    env = os.environ.copy()
    env["PATH"] = f"{NODE_PATH}:{env.get('PATH', '')}"
    return env

HTML_TEMPLATE_FULLSCREEN_DEMO = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{title}</title>
    <!-- GSAP for HyperFrames Deterministic Animation Engine -->
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }}
      body {{
        background: #000000;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        overflow: hidden;
      }}
      #root {{
        position: relative;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #000000;
      }}
      .clip {{
        position: absolute;
        inset: 0;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
      }}
      .fullscreen-media {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center top;
        display: block;
      }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-width="1080"
      data-height="1920"
      data-duration="{duration}"
    >
{audio_html}
      {screens_html}
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      {animations_js}

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

HTML_TEMPLATE_3D_SHOWCASE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0; padding: 0; background: #090a10; color: #ffffff;
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif; overflow: hidden;
      }}
      #root {{
        position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #090a10;
      }}
      .full-bg {{
        position: absolute; inset: 0;
        background: radial-gradient(circle at 50% 20%, #2a1b4e 0%, #0d0e17 60%, #05060a 100%);
        z-index: 0;
      }}
      .clip {{
        position: absolute; inset: 0; display: flex; flex-direction: column;
        align-items: center; justify-content: center; overflow: hidden; pointer-events: none;
      }}
      .phone-chassis {{
        position: relative; width: 520px; height: 1080px; border-radius: 54px;
        background: #000000; border: 7px solid #36363c;
        box-shadow: 0 0 0 2px #18181b, 0 35px 80px -15px rgba(0, 0, 0, 0.85);
        overflow: hidden; transform-style: preserve-3d;
      }}
      .phone-screen {{
        position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 46px;
      }}
      .dynamic-island {{
        position: absolute; top: 15px; left: 50%; transform: translateX(-50%);
        width: 130px; height: 35px; background: #000000; border-radius: 20px; z-index: 50;
      }}
      .banner-headline {{
        font-size: 64px; font-weight: 900; line-height: 1.05; text-align: center;
        text-transform: uppercase; margin: 20px 0 0 0; max-width: 920px;
      }}
      .voiceover-subtitle {{
        position: absolute; bottom: 120px; left: 50%; transform: translateX(-50%);
        width: 900px; padding: 24px 36px; background: rgba(13, 14, 23, 0.85);
        border-radius: 28px; font-size: 34px; font-weight: 600; text-align: center;
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-width="1080" data-height="1920" data-duration="{duration}">
      <audio id="narration" class="clip" data-start="0" data-duration="{duration}" data-volume="1.0" src="./assets/demo_narration.mp3"></audio>
      <div class="full-bg"></div>
      <section id="scene-phone" class="clip" data-start="0" data-duration="{duration}">
        <div class="phone-chassis">
          <div class="dynamic-island"></div>
          <img class="phone-screen" src="./assets/screen_01_upload.png" alt="Phone Screen" />
        </div>
      </section>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

def build_showcase(
    title: str,
    script_text: str,
    output_dir: Path,
    screenshots: list = None,
    audio_path: Path = None,
    demo_only: bool = True,
    render: bool = False
):
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Handle Screenshots
    staged_screens = []
    if screenshots:
        for idx, src in enumerate(screenshots, start=1):
            src_p = Path(src)
            dest = assets_dir / f"screen_{idx:02d}_{src_p.stem}.png"
            if src_p.exists() and src_p.resolve() != dest.resolve():
                shutil.copy(src_p, dest)
            staged_screens.append(dest.name)
    else:
        # Check existing screens
        existing = sorted([f.name for f in assets_dir.glob("screen_*.png")])
        staged_screens = existing if existing else ["screen_01_upload.png", "screen_02_voices.png", "screen_03_reader_light.png", "screen_04_reader_dark.png"]

    # 2. Audio Setup & Duration
    audio_html = ""
    if no_voice:
        if duration is None:
            duration = 15.0
    else:
        final_audio = assets_dir / "demo_narration.mp3"
        if audio_path and audio_path.exists() and audio_path.resolve() != final_audio.resolve():
            shutil.copy(audio_path, final_audio)
        elif not final_audio.exists():
            temp_aiff = assets_dir / "narration.aiff"
            subprocess.run(["say", "-v", "Samantha", "-r", "175", script_text, "-o", str(temp_aiff)], check=True)
            env = get_env()
            subprocess.run(["ffmpeg", "-y", "-i", str(temp_aiff), str(final_audio)], check=True, env=env)
            if temp_aiff.exists():
                temp_aiff.unlink()

        if duration is None:
            env = get_env()
            res = subprocess.run(
                ["ffprobe", "-i", str(final_audio), "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
                capture_output=True,
                text=True,
                env=env
            )
            duration = float(res.stdout.strip()) if res.stdout.strip() else 15.0
            duration = round(duration, 1)

        audio_html = f'''      <audio
        id="demo-audio"
        class="clip"
        data-start="0"
        data-duration="{duration}"
        data-volume="1.0"
        src="./assets/demo_narration.mp3"
      ></audio>'''

    if demo_only:
        # Fullscreen demo (no titles, no subtitles, no character)
        screen_count = max(1, len(staged_screens))
        step = duration / screen_count

        screens_html = []
        animations_js = []

        for i, sc in enumerate(staged_screens):
            s_start = round(i * step, 1)
            s_dur = round(step, 1)
            if i == len(staged_screens) - 1:
                s_dur = round(duration - s_start, 1)
            
            sc_id = f"phone-screen-{i+1}"
            screens_html.append(
                f'      <img id="{sc_id}" class="clip fullscreen-media" data-start="{s_start}" data-duration="{s_dur}" src="./assets/{sc}" alt="Screen {i+1}" />'
            )
            animations_js.append(
                f'      tl.fromTo("#{sc_id}", {{ scale: 1.0, y: 0 }}, {{ scale: 1.05, y: -30, duration: {s_dur}, ease: "none" }}, {s_start});'
            )

        html_content = HTML_TEMPLATE_FULLSCREEN_DEMO.format(
            title=title,
            duration=duration,
            audio_html=audio_html,
            screens_html="\n".join(screens_html),
            animations_js="\n".join(animations_js)
        )
    else:
        html_content = HTML_TEMPLATE_3D_SHOWCASE.format(
            title=title,
            duration=duration
        )

    (output_dir / "index.html").write_text(html_content, encoding="utf-8")

    # Write hyperframes.json
    config = {
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "duration": duration
    }
    (output_dir / "hyperframes.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[+] HyperFrames phone demo built at: {output_dir / 'index.html'} (Duration: {duration}s, Voice: {'None' if no_voice else 'Yes'})")

    if render:
        print("[*] Rendering MP4 via HyperFrames CLI...")
        render_dir = output_dir / "renders"
        render_dir.mkdir(parents=True, exist_ok=True)
        out_name = "voicereader_phone_demo_no_audio.mp4" if no_voice else "voicereader_phone_demo.mp4"
        out_mp4 = render_dir / out_name
        cmd = [
            "npx", "-y", "hyperframes", "render",
            "--workers", "1",
            "--output", str(out_mp4)
        ]
        subprocess.run(cmd, cwd=output_dir, env=env, check=True)
        print(f"[+] Render complete: {out_mp4}")

def main():
    parser = argparse.ArgumentParser(description="HyperFrames Phone Demo Video Generator")
    parser.add_argument("--title", default="VoiceReader App Phone Demo", help="Composition Title")
    parser.add_argument("--script", default="Finals are next week and you still have four hundred pages of mandatory reading left to finish.", help="Voiceover script text")
    parser.add_argument("--audio", type=Path, default=None, help="Optional pre-recorded audio file")
    parser.add_argument("--screenshots", help="Comma-separated screenshot paths")
    parser.add_argument("--duration", type=float, default=None, help="Target duration in seconds (default 15.0 or audio length)")
    parser.add_argument("--no-voice", "--no-audio", action="store_true", dest="no_voice", help="Render video without voice / audio track")
    parser.add_argument("--output-dir", type=Path, default=Path("./showcase"), help="Output directory")
    parser.add_argument("--demo-only", "--fullscreen", action="store_true", default=True, help="Render only the full-screen phone demo (no character, no titles, no subtitles)")
    parser.add_argument("--render", action="store_true", help="Render to MP4")

    args = parser.parse_args()
    sc_list = [s.strip() for s in args.screenshots.split(",")] if args.screenshots else None
    build_showcase(
        title=args.title,
        script_text=args.script,
        output_dir=args.output_dir.resolve(),
        screenshots=sc_list,
        audio_path=args.audio.resolve() if args.audio else None,
        duration=args.duration,
        no_voice=args.no_voice,
        demo_only=args.demo_only,
        render=args.render
    )

if __name__ == "__main__":
    main()
