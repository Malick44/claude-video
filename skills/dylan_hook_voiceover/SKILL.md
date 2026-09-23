---
name: dylan_hook_voiceover
version: "2.0.0"
description: "Generate viral 20-30s TikTok/Reels voiceover transcripts based on Dylan Page's high-retention hook formulas, 4-beat structure, and 172 WPM cadence. Generates clean transcripts to hand off to audio generation agents."
argument-hint: "<topic-or-story-text> [duration]"
allowed-tools: Bash, Read, AskUserQuestion
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /dylan_hook_voiceover

Generate mathematically calibrated, high-retention **20–30 second viral voiceover transcripts** engineered directly from the statistical patterns of TikTok creator **Dylan Page (@dylan.page)** (derived from an empirical dataset of his top 100 most hook-effective videos).

This skill is **purely dedicated to voiceover transcript generation** — removing all video and audio rendering so you can hand off the resulting script directly to an **audio generation agent** (TTS, ElevenLabs, Seed Audio) and video assembly tools (CapCut).

---

## Resolve `SKILL_DIR`

```bash
SKILL_DIR="<absolute path of directory containing this SKILL.md>"
```

---

## When to Use

- User provides a story topic, premise, news summary, or raw text (e.g. transcript from `/watch`) and needs a viral 20–30s short-form voiceover script.
- User needs a **clean spoken text transcript** (`clean_voiceover.txt`) to hand off to an audio generation agent or TTS engine.
- User needs beat-by-beat timestamps, vocal delivery instructions (`[Intense Whisper]`, `[Rapid-fire Matter-of-Fact]`), and on-screen banner titles.
- User needs an `.srt` subtitle file ready for video editors (CapCut Desktop, Premiere).

---

## Input Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `--topic` / `-t` | `string` | **Yes** | — | Core story topic, premise, or headline. |
| `--duration` / `-d` | `float` | No | `25.0` | Target duration in seconds (`20.0` to `30.0`). |
| `--input` / `-i` | `string` | No | — | Optional path to a text file containing story notes or raw transcript. |
| `--output-dir` / `-o` | `string` | No | — | Optional directory to save transcript files. |
| `--json` | `flag` | No | `false` | Output raw structured JSON to stdout. |

---

## Dylan Page's 4-Beat Viral Framework (Top 100 Empirical Data)

Pacing and narrative architecture adhere to Dylan Page's proven formula:

- **Cadence:** **168 – 175 Words Per Minute (WPM)**. Average: **172 WPM**.
- **Strict Word Count Limits:**
  - **20s:** 55 – 58 words
  - **25s:** 70 – 74 words
  - **30s:** 82 – 86 words
  *(Never exceed 86 words for a 30s video, or rapid delivery becomes unintelligible).*

```
[0.0s ──────────────── 3.2s]  Beat 1: Scroll-Stop Hook (8-12 words)
[3.2s ──────────────── 9.5s]  Beat 2: Setup & Entities (18-22 words)
[9.5s ─────────────── 22.0s]  Beat 3: Escalation & Dramatic Twist (28-36 words)
[22.0s ────────────── 30.0s]  Beat 4: Moral Dilemma / Outro Question (12-16 words)
```

### Beat 1: The Scroll-Stop Hook (0.0s – 3.2s)
- **Objective:** Pattern interrupt to stop mindless feed scrolling within 3 seconds.
- **Top Empirical Archetypes:**
  1. *Absurd Shock:* "This might actually be the most unbelievable thing you see all week..."
  2. *Urgent Warning:* "Bro we are in so much trouble..." / "Do NOT do this..."
  3. *Unbelievable Contrast:* "We don't deserve Japan..." / "Someone actually built..."
  4. *Moral Dilemma:* "Is this creepy or useful?" / "What would you do here?"
- **Vocal Cue:** `[Intense Whisper / Shocked Eye Contact / Sudden Peak]`
- **Banner Title:** Punchy 4-6 word headline (e.g. `WORST GUARD DOG IN HISTORY?`).

### Beat 2: The Setup & Entities (3.2s – 9.5s)
- **Objective:** Establish the protagonist, location, and immediate stakes in one breath.
- **Vocal Cue:** `[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]`
- **Banner Title:** Context summary (e.g. `CAUGHT ON SECURITY CAMERA...`).

### Beat 3: The Escalation & Dramatic Twist (9.5s – 22.0s)
- **Objective:** "Things take an unexpected turn." Reveal the irony, conflict, or bizarre climax.
- **Vocal Cue:** `[Incredulous Pause / Pitch Shift / Shocked Delivery]`
- **Banner Title:** The turning point (e.g. `DOG BROUGHT HIM A TOY 3 TIMES!`).

### Beat 4: The Moral Dilemma / Outro Question (22.0s – 30.0s)
- **Objective:** Force viewers into the comment section to debate, driving algorithmic distribution.
- **Signature Closers:** "So let me know down below... what would you have done?", "Would you fire this dog?", "Who is in the wrong here?"
- **Vocal Cue:** `[Deadpan Delivery / Eyebrow Raise / Direct Gaze]`
- **Banner Title:** Engagement question (e.g. `WOULD YOU FIRE THIS DOG?!`).

---

## Running the Engine

### CLI Command

```bash
# Generate transcript for a topic and save outputs
python3 "${SKILL_DIR}/scripts/craft_hook_voiceover.py" \
  --topic "a golden retriever welcoming a burglar with a toy during a break-in" \
  --duration 25 \
  --output-dir "./output_transcript"
```

### Output Files Produced

1. **`clean_voiceover.txt`** — Clean spoken text only, with no timestamps or bracketed cues. Pass this directly to your audio generation agent (TTS / ElevenLabs / Seed Audio).
2. **`voiceover_transcript.txt`** — Full human-readable transcript with second-by-second timestamps, vocal inflection cues, and on-screen banner titles.
3. **`transcript.srt`** — SubRip subtitle file with exact beat timestamps for video editors (CapCut, Premiere).
4. **`transcript.json`** — Structured JSON payload with beat boundaries, word counts, banner headlines, and per-beat vocal `tone` instructions for audio cloning agents (`auk_voiceover`).

---

## Agent Handoff Flow

```
[ User Premise / Topic / Watch Video Transcript ]
                       │
                       ▼
         /dylan_hook_voiceover
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
  clean_voiceover.txt         transcript.srt
         │                           │
         ▼                           ▼
[ Audio Generation Agent ]    [ CapCut Video Assembler ]
  (TTS / ElevenLabs)           (Project 0916 / Split)
```
