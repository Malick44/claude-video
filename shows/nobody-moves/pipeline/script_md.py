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
    title = " ".join(w[:1].upper() + w[1:].lower() for w in ep.EPISODE.split(":", 1)[-1].split())  # "It's", not "It'S"
    out = [
        f"# {ep.TITLE}, {ep.EPISODE.split(':')[0].title()}: \"{title}\"\n",
        f"Runtime: **{tl['total']:.1f}s**, 9:16 vertical, 1080×1920 at 30 fps.\n",
    ]
    if getattr(ep, "ANSWER", None):
        out.append(f"**Cliffhanger answer (don't post this):** {ep.ANSWER}\n")
    out += ["## Voices\n", "| Character | Voice |", "|---|---|"]
    speakers = {c["who"] for c in tl["captions"]}
    for who, c in ep.CAST.items():
        if who not in speakers:
            continue
        extra = []
        if c.get("pitch", 1.0) != 1.0:
            extra.append(f"pitch ×{c['pitch']}")
        if c.get("altered"):
            extra.append("disguised")
        voice = f"ElevenLabs {c['voice_id']}" if c.get("provider") == "elevenlabs" else f"Kokoro {c['voice']}"
        out.append(f"| {who} | {voice}" + (f" ({', '.join(extra)})" if extra else "") + " |")
    recorded = sum(c.get("recorded", False) for c in tl["captions"])
    out += ["", "To use your own take for a line, save it as `recordings/<name>.m4a` (or .wav/.mp3) in this "
            f"episode folder, using the name shown next to the line. {recorded} of {len(tl['captions'])} lines are recorded.",
            "", "## Script\n"]
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
                mark = "recorded" if c.get("recorded") else "record as"
                out.append(f"\n**{c['who']}** ({tc(c['start'])}) · {mark} `{c.get('rec', '')}`: {c['text']}")
        out.append("")
    if tl.get("credits"):
        out += ["## Credits\n", "Stock sounds used in this episode. Paste the Attribution (CC-BY) ones into the TikTok description.\n"]
        for c in tl["credits"]:
            parts = [c.get("title", ""), f"by {c['author']}" if c.get("author") else "", c.get("license", ""), c.get("source", "")]
            out.append("- " + " · ".join(p for p in parts if p))
        out.append("")
    path = os.path.join(ep.DIR, "SCRIPT.md")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
