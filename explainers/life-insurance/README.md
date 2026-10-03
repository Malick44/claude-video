# Life insurance explainer (Remotion)

A ~110 s, 1920×1080, 30 fps motion-graphics explainer: **why life insurance matters for millennial
homeowners sandwiched between aging parents and young kids.** Independent of the `watch` skill.

## Story

| # | Scene | What it shows |
|---|-------|---------------|
| – | Hook | Slam-cut kinetic type (Mortgage. Daycare. Mom's prescriptions…) → "You're the load-bearing wall" → house with a cracking beam |
| 01 | The squeeze | Three-generation panels press in on "you"; $4,800/mo of obligations tick up on one income |
| 02 | The risk | Paycheck coin-stream stops; bills keep running; emergency fund drains |
| 03 | Your number | DIME method (Debt, Income, Mortgage, Education) builds a $1.33M coverage tower |
| 04 | The price | ~$50/mo term-life price card + "what waiting costs" bar chart (age 30 → 50) |
| 05 | The fit | Gantt of mortgage / kids / parents' care vs. a 30-year level term; term vs. permanent |
| 06 | Myths vs. facts | 3D flip cards: employer coverage, "later", stay-at-home partner, taxes |
| 07 | Get it done | 4-step stepper that fills in an illustrative policy card, with a stamp |
| – | Close | House → shield path morph, family inside, CTA, disclaimer |

Motion toolkit used: spring physics, per-word kinetic type (blur/rise/tilt), SVG path drawing
(`evolvePath`), path morphing (`interpolatePath`), animated counters and charts, 3D card flips,
parallax/camera push-ins, `TransitionSeries` with slide/fade/wipe/clock-wipe/flip, animated gradient
and particle backgrounds, a synthesized score with scene-locked SFX, and a Kokoro voiceover that ducks the music.

All dollar figures are **illustrative** (and labelled as such on screen). The video is educational,
not financial or insurance advice.

## Run

```bash
cd explainers/life-insurance
npm install
python3 scripts/make_score.py   # needs numpy + ffmpeg; writes public/score.mp3
# Voiceover (Kokoro, same pinned model files as shows/nobody-moves/tools/common.sh):
KOKORO_MODELS=~/.kokoro/models python3 scripts/make_voiceover.py   # writes public/vo.mp3 + src/vo.json
npm run studio                  # live preview
npm run render                  # -> out/explainer.mp4
```

Scene lengths live in `src/timeline.json`; the composition, score and voiceover generators all read it.
Narration cues in `make_voiceover.py` are scene-relative frames, so after retiming a scene just re-run
`make_score.py` and `make_voiceover.py`. `src/vo.json` drives the music ducking in `Explainer.tsx`.

The rendered video is published as a GitHub release asset, not committed to the repo.
Fonts (Fraunces, Inter) are vendored in `public/fonts`, so renders work offline.
