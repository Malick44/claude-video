"""Write <episode>/SCRIPT.md (timecoded script) from episode.py + build/timeline.json.

  python pipeline/script_md.py episodes/<episode>

SCRIPT.md is rewritten on every build, so hand-written notes go in the episode's NOTES.md (linked
under the header when it exists). An episode's HUMAN_TAKES (rec -> one line of direction, or a list
of recs) stars those lines and lists them, as the fallback when a TTS voice can't land them.
Reenactment shots show their clip, length, speed, label and stamp, and a "Reenactment clips" section
lists each clip's generator, prompt and credit from clips.json, for the post's AI disclosure. The Voices
table names the voice each character's lines were built with (timeline.json), and counts locked v4 takes
(recordings/<rec>.v4.*) apart from human recordings.
"""
import json
import os
import re
import sys

from common import CLIP_KINDS, clip_path, fmt_rate, load_episode
from stock import TTS_MODEL


def tc(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def clip_line(s):
    """The reenactment's clip, under its heading."""
    length = s["end"] - s["start"]
    out = s["clip_in"] + length * s["clip_speed"]          # the part played: "dur" can cut before "out"
    if s.get("clip_out") is not None:
        out = min(out, s["clip_out"])
    line = (f"> REENACTMENT: clip `{s['clip']}` · {length:.2f} s at {fmt_rate(s['clip_speed'])}x (source {s['clip_in']:.2f}–"
            f"{out:.2f} s) · \"{s['label']}\"" + (f" · stamp \"{s['stamp']}\"" if s.get("stamp") else ""))
    if s.get("clip_missing"):
        line += (f" · CLIP MISSING, fallback still `{s['clip_fallback']}`" if s.get("clip_fallback")
                 else " · CLIP MISSING, no fallback still")
    return line


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: script_md.py episodes/<episode>")
    ep = load_episode(sys.argv[1])
    with open(os.path.join(ep.BUILD, "timeline.json")) as f:
        tl = json.load(f)
    # title-case each word from its first letter or digit, so "It's" (not "It'S") and "(Reenacted)"
    title = " ".join(w[:i] + w[i:i + 1].upper() + w[i + 1:].lower()
                     for w in ep.EPISODE.split(":", 1)[-1].split() for i in [re.match(r"\W*", w).end()])
    out = [
        f"# {ep.TITLE}, {ep.EPISODE.split(':')[0].title()}: \"{title}\"\n",
        f"Runtime: **{tl['total']:.1f}s**, 9:16 vertical, 1080×1920 at 30 fps.\n",
    ]
    if getattr(ep, "ANSWER", None):
        out.append(f"**Cliffhanger answer (don't post this):** {ep.ANSWER}\n")
    notes = os.path.exists(os.path.join(ep.DIR, "NOTES.md"))
    if notes:
        out.append("Build notes, timing and laughs, canon checks, recording direction and the review log: "
                   "[NOTES.md](NOTES.md).\n")
    human = getattr(ep, "HUMAN_TAKES", None) or {}
    if not isinstance(human, dict):
        human = {rec: None for rec in human}
    out += ["## Voices\n", "| Character | Voice |", "|---|---|"]
    speakers = {c["who"] for c in tl["captions"]}
    for who, c in ep.CAST.items():
        if who not in speakers:
            continue
        mine = [x for x in tl["captions"] if x["who"] == who]
        built = next((x for x in mine if x.get("provider") == "elevenlabs"), None)
        fx = c if (built is None) == (c.get("provider") != "elevenlabs") else {}   # the cast's FX, if it built them
        extra = []
        if fx.get("pitch", 1.0) != 1.0:
            extra.append(f"pitch ×{fx['pitch']}")
        if fx.get("altered"):
            extra.append("disguised")
        # The voice the soundtrack was built with, from timeline.json (build_audio.py marks every ElevenLabs line
        # and every locked v4 take), so a run under another NM_VOICES than the build's still names the right one;
        # the cast fills in only what a Kokoro line doesn't record (its preset).
        on_kokoro = any(not x.get("recorded") and not x.get("provider") for x in mine)
        locked = sum(1 for x in mine if x.get("generated"))
        if built:
            voice = f"ElevenLabs {built['voice_id']} on {built['model']}"
        elif on_kokoro:
            voice = (f"Kokoro {c['voice']}" if c.get("provider", "kokoro") == "kokoro"
                     else "Kokoro (the scratch cast; this cast entry is ElevenLabs now: rebuild the audio)")
        elif locked:
            voice = "ElevenLabs"
        elif c.get("provider") == "elevenlabs":
            voice = f"ElevenLabs {c['voice_id']} on {c.get('model', TTS_MODEL)}"
        else:
            voice = f"Kokoro {c['voice']}"
        if locked:
            extra.append(f"{locked} locked v4 take{'s' if locked > 1 else ''}")
        out.append(f"| {who} | {voice}" + (f" ({', '.join(extra)})" if extra else "") + " |")
    locked = sum(c.get("generated", False) for c in tl["captions"])
    recorded = sum(c.get("recorded", False) for c in tl["captions"]) - locked
    out += ["", "To use your own take for a line, save it as `recordings/<name>.m4a` (or .wav/.mp3) in this "
            f"episode folder, using the name shown next to the line. {recorded} of {len(tl['captions'])} lines are recorded."]
    if locked:
        out[-1] += (f" {locked} more {'is a locked v4 take' if locked == 1 else 'are locked v4 takes'} "
                    "(`recordings/<name>.v4.wav`), which count as AI voices on the end card; a human take of the same "
                    "line replaces one.")
    if any(c.get("tags") for c in tl["captions"]):
        out[-1] += (" A *(direction)* in italics after a line lists the audio tags its voice was given, the "
                    "delivery to aim for in your own take. Only an ElevenLabs voice on a model that takes tags "
                    "(eleven_v4) acts on them.")
    out += ["", "## Script\n"]
    for s in tl["shots"]:
        out.append(f"### {tc(s['start'])}–{tc(s['end'])} · {s['id'].upper()}")
        if s["kind"] in CLIP_KINDS:
            out.append(clip_line(s) + "\n")
        if s.get("note"):
            out.append(s["note"])
        if s.get("lower_third"):
            a, b, c = s["lower_third"]
            out.append(f"\n> Lower third: **{a}**, {b}, *{c}*")
        if s["kind"] == "qcard":
            out.append(f"\n> **Q:** {s['text']}")
        for c in tl["captions"]:
            if c["shot"] == s["id"]:
                mark = "v4 take" if c.get("generated") else "recorded" if c.get("recorded") else "record as"
                direction = f" *({', '.join(t[1:-1] for t in c['tags'])})*" if c.get("tags") else ""
                star = " ★" if c.get("rec") in human else ""
                out.append(f"\n**{c['who']}** ({tc(c['start'])}) · {mark} `{c.get('rec', '')}`{star}: {c['text']}{direction}")
        out.append("")
    used = []
    for s in tl["shots"]:
        if s["kind"] in CLIP_KINDS and s["clip"] not in [k for k, _ in used]:
            used.append((s["clip"], s))
    if used:
        out += ["## Reenactment clips\n", "Generated with AI. For the post description's AI disclosure and credits.\n"]
        for key, s in used:
            path = clip_path(ep.DIR, key)
            index = os.path.join(os.path.dirname(path), "clips.json") if path else None
            entry = (json.load(open(index)) if index and os.path.exists(index) else {}).get(key)
            if entry:
                parts = [f"{entry.get('generator') or 'generator not recorded'}"]
                if entry.get("credit"):
                    parts.append(f"credit: {entry['credit']}")
                out.append(f"- `{key}` ({s['id']}): " + "; ".join(parts) + f". Prompt: {entry.get('prompt', '')}")
            else:
                status = "filed without a clips.json entry" if path else "not filed yet; the shot renders its fallback still"
                if s.get("blender") and not path:
                    status = (f"rendered by pipeline/blender_reenact.py ({s['blender'].get('template')}), not filed "
                              "yet; the shot renders its fallback still")
                prompt = getattr(ep, "CLIPS", {}).get(key)
                out.append(f"- `{key}` ({s['id']}): {status}." + (f" Prompt (CLIPS): {prompt}" if prompt else ""))
        out.append("")
    if human:
        out += ["## Lines to record by a human\n",
                "The fallback: a line goes to a human only when its TTS voice can't land it after 3 tries. These are "
                "the likeliest, in this order, each with its direction." + (" Same-session companions and the length "
                                                                           "rule are in NOTES.md." if notes else "") + "\n"]
        lines = {c.get("rec"): c for c in tl["captions"]}
        for i, (rec, how) in enumerate(human.items(), 1):
            c = lines.get(rec)
            what = how or (f"{c['who']}, \"{c['text']}\"" if c else "not a line in this episode")
            out.append(f"{i}. `{rec}`: {what}")
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
