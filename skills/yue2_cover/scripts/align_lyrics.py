#!/usr/bin/env python3
"""Audit and align lyrics syllables against an ABC melody score.

Pure Python standard-library implementation. Analyzes note counts per
section in score.abc and compares against syllable counts in lyrics (txt or json).
"""

import argparse
import json
import re
import sys
from pathlib import Path


def count_syllables_word(word: str) -> int:
    """Heuristic English syllable counter."""
    word = word.lower().strip()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    
    special = {
        "the": 1, "you": 1, "fire": 1, "hour": 1, "our": 1,
        "world": 1, "rhythm": 2, "prism": 2, "every": 2,
    }
    if word in special:
        return special[word]

    if word.endswith("e") and not word.endswith("le") and not word.endswith("ee"):
        word = word[:-1]
    elif word.endswith("ed") and not word.endswith("ted") and not word.endswith("ded"):
        word = word[:-2]

    count = len(re.findall(r"[aeiouy]+", word))
    return max(1, count)


def count_syllables_line(line: str) -> int:
    words = [w for w in re.split(r"\s+", line) if w]
    return sum(count_syllables_word(w) for w in words)


def parse_abc_sections(abc_text: str) -> list[dict]:
    sections = []
    current_sec = {"name": "Intro / Unlabeled", "notes": 0}
    
    in_vocal = False
    for line in abc_text.splitlines():
        line = line.strip()
        if line.startswith("% "):
            sec_name = line[2:].strip().title()
            if current_sec["notes"] > 0 or current_sec["name"] != "Intro / Unlabeled":
                sections.append(current_sec)
            current_sec = {"name": sec_name, "notes": 0}
            in_vocal = False
            continue
            
        if line.startswith("V: Vocal"):
            in_vocal = True
            continue
        elif line.startswith("V: Ins"):
            in_vocal = False
            continue
            
        if in_vocal and line and not line.startswith(("M:", "K:", "L:", "Q:", "V:", "X:", "T:")):
            tokens = re.findall(r'"[^"]*"|[A-Ga-gz][,\']*', line)
            for tok in tokens:
                if tok.startswith('"') or tok.startswith('z'):
                    continue
                current_sec["notes"] += 1

    if current_sec["notes"] > 0 or not sections:
        sections.append(current_sec)
    return sections


def parse_lyrics_sections(lyrics_text: str) -> list[dict]:
    # If JSON, extract "lyrics" field
    try:
        data = json.loads(lyrics_text)
        if isinstance(data, dict) and "lyrics" in data:
            lyrics_text = data["lyrics"]
    except Exception:
        pass

    # Normalize escape sequences if needed
    lyrics_text = lyrics_text.replace("\\n", "\n")

    sections = []
    current_sec = {"name": "General", "lines": [], "total_syllables": 0}
    
    for raw_line in lyrics_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.fullmatch(r"\[([A-Za-z0-9 _-]+)\]", line)
        if match:
            if current_sec["lines"]:
                sections.append(current_sec)
            current_sec = {"name": match.group(1).title(), "lines": [], "total_syllables": 0}
        else:
            syl = count_syllables_line(line)
            current_sec["lines"].append({"text": line, "syllables": syl})
            current_sec["total_syllables"] += syl

    if current_sec["lines"]:
        sections.append(current_sec)
    return sections


def audit(abc_path: Path, lyrics_path: Path) -> dict:
    abc_text = abc_path.read_text(encoding="utf-8")
    lyrics_text = lyrics_path.read_text(encoding="utf-8")
    
    abc_secs = parse_abc_sections(abc_text)
    lyr_secs = parse_lyrics_sections(lyrics_text)
    
    # Filter out empty intro sections from score if lyrics don't have an intro
    active_abc = [s for s in abc_secs if s["notes"] > 0]
    if not active_abc:
        active_abc = abc_secs

    total_notes = sum(s["notes"] for s in active_abc)
    total_syllables = sum(s["total_syllables"] for s in lyr_secs)
    
    comparisons = []
    max_secs = max(len(active_abc), len(lyr_secs))
    for i in range(max_secs):
        asec = active_abc[i] if i < len(active_abc) else {"name": "N/A", "notes": 0}
        lsec = lyr_secs[i] if i < len(lyr_secs) else {"name": "N/A", "total_syllables": 0, "lines": []}
        
        diff = lsec.get("total_syllables", 0) - asec.get("notes", 0)
        if diff == 0:
            status = "PERFECT_MATCH"
            advice = "1:1 syllable-to-note mapping."
        elif diff < 0:
            status = "UNDER_SYLLABLES"
            advice = f"{abs(diff)} notes will hold melismas (vowels stretched across multiple notes)."
        else:
            status = "OVER_SYLLABLES"
            advice = f"{diff} extra syllables. Singer may cram or drop syllables; consider shortening."
            
        comparisons.append({
            "score_section": asec.get("name"),
            "notes": asec.get("notes"),
            "lyric_section": lsec.get("name"),
            "syllables": lsec.get("total_syllables"),
            "status": status,
            "advice": advice,
            "lines": lsec.get("lines", [])
        })

    return {
        "total_melody_notes": total_notes,
        "total_lyric_syllables": total_syllables,
        "overall_fit": "BALANCED" if abs(total_notes - total_syllables) <= 4 else ("TIGHT" if total_syllables > total_notes else "SPACIOUS"),
        "sections": comparisons
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path, help="Clean melody score.abc")
    parser.add_argument("lyrics", type=Path, help="Text or JSON file containing lyrics with [Section] headers")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output")
    args = parser.parse_args()

    result = audit(args.score, args.lyrics)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("  LYRIC-TO-MELODY SYLLABLE ALIGNMENT AUDIT")
        print("=" * 60)
        print(f"Total Vocal Notes:     {result['total_melody_notes']}")
        print(f"Total Lyric Syllables: {result['total_lyric_syllables']}")
        print(f"Overall Fit:           {result['overall_fit']}\n")
        
        for sec in result["sections"]:
            print(f"▶ Section: Score [{sec['score_section']}] ({sec['notes']} notes) vs Lyrics [{sec['lyric_section']}] ({sec['syllables']} syl)")
            print(f"  Status: {sec['status']} — {sec['advice']}")
            for line in sec["lines"]:
                print(f"    • ({line['syllables']} syl) \"{line['text']}\"")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
