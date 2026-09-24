"""Write <episode>/SCRIPT.md (timecoded script) from episode.py + build/timeline.json.

  python pipeline/script_md.py episodes/<episode>
"""
import json
import os
import sys

from common import load_episode


def tc(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: script_md.py episodes/<episode>")
    ep = load_episode(sys.argv[1])
    with open(os.path.join(ep.BUILD, "timeline.json")) as f:
        tl = json.load(f)
    title = ep.EPISODE.split(":", 1)[-1].strip().title()
    out = [
        f"# {ep.TITLE}, {ep.EPISODE.split(':')[0].title()}: \"{title}\"\n",
        f"Runtime: **{tl['total']:.1f}s**, 9:16 vertical, 1080×1920 at 30 fps.\n",
    ]
    if getattr(ep, "ANSWER", None):
        out.append(f"**Cliffhanger answer (don't post this):** {ep.ANSWER}\n")
    out += ["## Voices\n", "| Character | Scratch voice (Kokoro TTS) |", "|---|---|"]
    for who, c in ep.CAST.items():
        extra = []
        if c.get("pitch", 1.0) != 1.0:
            extra.append(f"pitch ×{c['pitch']}")
        if c.get("altered"):
            extra.append("disguised")
        out.append(f"| {who} | {c['voice']}" + (f" ({', '.join(extra)})" if extra else "") + " |")
    out += ["", "## Script\n"]
    for s in tl["shots"]:
        out.append(f"### {tc(s['start'])}–{tc(s['end'])} · {s['id'].upper()}")
        if s.get("note"):
            out.append(s["note"])
        if s.get("lower_third"):
            a, b, c = s["lower_third"]
            out.append(f"\n> Lower third: **{a}**, {b}, *{c}*")
        if s["kind"] == "qcard":
            out.append(f"\n> **Q:** {s['text']}")
        for c in tl["captions"]:
            if c["shot"] == s["id"]:
                out.append(f"\n**{c['who']}** ({tc(c['start'])}): {c['text']}")
        out.append("")
    path = os.path.join(ep.DIR, "SCRIPT.md")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
