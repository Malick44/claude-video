---
name: yue2_cover
version: "0.1.0"
description: Generate a new song or cover from a reference audio file or URL using local YuE2 and custom lyrics. Extracts vocal melody via SheetSage2 to ABC, strips chords, checks and fits lyric syllables to melody notes, and renders the new song with local YuE2 models.
argument-hint: "<audio-or-url> [style] [lyrics-file]"
allowed-tools: Bash, Read, AskUserQuestion
license: MIT
user-invocable: true
---

# /yue2_cover

Turn any reference song (audio file or URL) into a brand-new song using your own lyrics and your local **YuE2** models (`models/YuE2-3B` and `models/YuE2-Vae`).

The skill extracts the vocal melody into an ABC notation score, strips chords so the melody is clean, checks that your lyric syllables fit the melody notes, and renders the new song with YuE2 using `cot="melody"`.

---

## Resolve `SKILL_DIR`

Before running any bundled scripts, set `SKILL_DIR` to the directory containing this `SKILL.md`:

```bash
SKILL_DIR="<absolute path of directory containing this SKILL.md>"
```

All bundled scripts are located in `${SKILL_DIR}/scripts/`.

---

## When to Use

- User provides a reference song (MP3, WAV, FLAC, or YouTube/streaming URL) and wants to make a new version/cover in a different style.
- User has written original lyrics and wants them sung to the tune of an existing reference track.
- User wants to extract, inspect, or align lyric syllables against a reference melody before generating audio.
- User wants to execute local YuE2 generation with `cot="melody"`.

---

## Input Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `audio` | `string` | **Yes** | Path to local audio file (`.wav`, `.mp3`, `.flac`) or public URL. |
| `style` | `string` | **Yes** | Target genre, instruments, vocals, and BPM (e.g. `"English, modern jazz, female vocal, upright bass, piano, 88 BPM"`). |
| `lyrics` | `string` | **Yes** | Text file path (`.txt` or `.json`) or raw string with section tags (`[Verse]`, `[Chorus]`). |
| `output` | `path` | No | Destination directory for outputs (default: `outputs/cover_<id>`). |
| `device` | `string` | No | Target device: `mps` (Mac default), `cuda` (NVIDIA), or `cpu`. |

---

## Method 1: All-in-One Command

You can run the full end-to-end pipeline in one step:

```bash
python3 "${SKILL_DIR}/scripts/produce_cover.py" \
  --audio "/path/to/reference_song.mp3" \
  --style "English, acoustic piano pop, soulful female vocal, warm bass, 95 BPM" \
  --lyrics "/path/to/lyrics.txt" \
  --output "outputs/my_cover" \
  --device mps
```

This automatically:
1. Downloads audio (if a URL is provided).
2. Transcribes the vocal melody using SheetSage2.
3. Strips chord symbols to produce `clean_melody.abc`.
4. Audits lyric syllables against melody notes and prints the alignment report.
5. Formats `request.json` with `cot="melody"`.
6. Generates the audio using local `YuE2-3B` and `YuE2-Vae`.
7. Converts the final audio to a pristine, uncompressed `.wav` file (`outputs/my_cover/<id>.wav`).

---

## Method 2: Step-by-Step Interactive Workflow

If you want full control over each stage (e.g. to tweak the melody or adjust lyric words after seeing the syllable audit):

### Step 1: Transcribe Vocal Melody to ABC
Run SheetSage2 transcription:
```bash
python /Users/malickdes/AIWORKSPACE/YuE-music/skills/yue2-music/scripts/transcribe.py \
  /path/to/reference.wav \
  --task melody-vocal \
  --output outputs/transcription
```
*Outputs:* `outputs/transcription/score.abc`.

### Step 2: Strip Chords for Melodic Freedom
Remove chord symbols so YuE2 is free to arrange new harmonies in your target genre:
```bash
python3 "${SKILL_DIR}/scripts/abc_tools.py" strip-chords \
  outputs/transcription/score.abc \
  outputs/clean_melody.abc \
  --keep-voice Vocal
```

### Step 3: Audit Syllable Alignment
Verify whether the user's lyrics match the note count and phrase structure:
```bash
python3 "${SKILL_DIR}/scripts/align_lyrics.py" \
  outputs/clean_melody.abc \
  /path/to/lyrics.txt
```
- **If OVER_SYLLABLES:** Flag to user that syllables exceed notes; propose trimmed wording to prevent lyric cramping.
- **If UNDER_SYLLABLES:** Notes will hold natural melismas (vowel extensions).
- **If BALANCED:** Ready for synthesis!

### Step 4: Run YuE2 Generation
Execute local generation using the clean ABC score and user lyrics:
```bash
/Users/malickdes/AIWORKSPACE/YuE-music/.venv/bin/python \
  /Users/malickdes/AIWORKSPACE/YuE-music/skills/yue2-music/scripts/run_yue2.py generate \
  --request outputs/request.json \
  --abc-file outputs/clean_melody.abc \
  --cot melody \
  --output outputs/my_cover_song \
  --model /Users/malickdes/AIWORKSPACE/YuE-music/models/YuE2-3B \
  --vae /Users/malickdes/AIWORKSPACE/YuE-music/models/YuE2-Vae \
  --offline \
  --device mps
```

### Step 5: Deliver Playback & Export WAV
Convert the generated FLAC to WAV and provide playback instructions:
```bash
# Convert FLAC to high-fidelity 24-bit 48kHz WAV
python3 -c "import soundfile as sf; d, sr = sf.read('outputs/my_cover_song/audio.flac'); sf.write('outputs/my_cover_song/cover_song.wav', d, sr, subtype='PCM_24')"

# Test playback
afplay outputs/my_cover_song/cover_song.wav
```

---

## Important Rules for the Agent

1. **Never pass audio directly to YuE2:** YuE2 has no audio reference argument; always bridge audio through SheetSage2 ABC transcription.
2. **Always strip chords for a cover:** `cot="melody"` requires chord-free ABC. If chord symbols remain, `run_yue2.py` will reject the file.
3. **Audit lyrics before generating:** Check the syllable report before running generation. Alert the user if a verse has twice as many syllables as there are notes.
4. **Mac / Apple Silicon stability:** Default to `--device mps`. If non-finite latent errors or FP8 kernel issues occur, switch to `--device cpu`.
