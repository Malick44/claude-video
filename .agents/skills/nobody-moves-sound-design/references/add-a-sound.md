# Worked example: adding a new named sound

This walks the full path for a new synthesized sound, `gavel`: Mr. Basin's ruling after his "no comment". Every step below was run on a scratch copy of the show with ep02's `basin` shot using it. It built, exported and measured cleanly. The step numbers match recipe (b) in SKILL.md.

## 1. Generator: `pipeline/sounds.py`

Put it with the foley, before `glitch()`:

```python
def gavel():
    """Courtroom gavel: two hard wooden knocks with a short body resonance, in the show's hall."""
    rng = _rng("gavel")
    t = t_axis(0.9)
    y = np.zeros_like(t)
    for at, g in ((0.0, 1.0), (0.16, 0.7)):
        s = int(at * SR)
        tt = t[: len(t) - s]
        knock = bandpass(rng.normal(0, 1, len(tt)), 600, 5000) * np.exp(-tt * 70)
        body = np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 25) + 0.5 * np.sin(2 * np.pi * 410 * tt) * np.exp(-tt * 35)
        y[s:] += g * (knock + 0.8 * body)
    return normalize(reverb(y, 1.5, 0.25))
```

- **Seed:** the random stream is `_rng("gavel")`. The key is the sound's name plus any parameter that changes it, for example `_rng("gavel", dur)` if it took a duration.
- **Level:** it returns peak-normalized audio. Loudness lives only in `LEVELS`.
- **Room:** it goes through `reverb()`, so it sits in the same hall as everything else.
- **Phone speakers:** it has body at 180 and 410 Hz, above the phone cutoff. A sub-only thump would vanish on a phone.

## 2. Resolver: `pipeline/soundbank.py`

```python
SYNTH = {
    ...
    "jump": lambda sec, i: snd.jump(),
    "gavel": lambda sec, i: snd.gavel(),
}
```

- **Loops:** if the sound is a bed that must fill a shot, have the generator take `sec`, and add the name to `LOOPED` so a stock replacement is fit to length too.
- **Docstring:** add the name to the "Names:" list at the top of the file.

## 3. Level: `LEVELS` in `pipeline/sounds.py`

```python
    "gavel": -4,         # Mr. Basin's ruling, after his shot's last line
```

Pick the number by measurement, not by guess:

```bash
.venv/bin/python $PROBE gavel shutter jump
# gavel at -12:  0.5s -20.6  placed -32.6   <- quieter than the jump; too quiet for a ruling
# shutter:       placed -32.0 (its impact, at -4, is what you hear: placed about -20)
# jump:          placed -28.2
```

The first guess, -12, looked sensible, but the probe showed the knock's loudest 0.5 s is 20.6 dB below full scale: its energy is two brief transients. At -12 it would sit under the doorbell jump and fall out of the hit list. At -4 it is placed at -24.6, between the shutter hit and the jump, which suits a punctuation mark after a line.

## 4. Placement: `pipeline/build_audio.py`

**Chosen per shot:** add a branch to the `for name in s.get("sfx", []):` chain, before the ambiences:

```python
            elif name == "gavel":
                # after the shot's last line (the ruling lands on the silence)
                at = s["lines"][-1]["end"] + 0.1 if s["lines"] else s["start"]
                put(fxbus, at, bank.get("gavel"), LEVELS["gavel"])
```

**Automatic:** put it under an `if s["kind"] == ...:` block instead, as the whoosh, glitch and jump are.

Pick the bus by what should happen under dialogue:
- `fxbus`: hits and foley. Never ducked, never cut by `"music": "out"`.
- `under`: tonal builds such as risers and swells. Ducked under dialogue, but also not cut by `"music": "out"`. mixcheck counts it as score, so an `under` sound inside a music-out shot fails the music-out check.
- `score`: holds only the theme bed. Don't add to it.

## 5. Label it in `pipeline/mixcheck.py`

Add the cue in `cues()`, so the hit list names it:

```python
        if "gavel" in sfx:
            at = s["lines"][-1]["end"] + 0.1 if s.get("lines") else s["start"]
            out.append((at, "gavel", LEVELS["gavel"]))
```

If the sound goes on `under` instead, the hit list never sees it (it reads only the effects stem). Add it to `placed_over()` in this skill's `scripts/soundprobe.py`, next to `sting_soft` and the risers, so `soundprobe.py --lines` names it when it sits under a line.

## 6. Kit: `KIT` in `pipeline/sound_kit.py`

```python
    "gavel": lambda: bank.get("gavel"),
```

## 7. Docs

Every list of sound names has to stay in sync. The error messages and the write skill point users at these lists:

- `soundtrack.py`, docstring "Names:".
- `pipeline/soundbank.py`, docstring "Names:".
- `shows/nobody-moves/README.md`:
  - the "Score and sound effects" table (one row: how it's made);
  - the `sfx` options sentence under the `episode.py` reference table, if it's chosen per shot;
  - the names list in "Stock assets";
  - the sound-kit bullet list.
- If it's chosen per shot, the write skill: `.agents/skills/nobody-moves-write-episode/references/episode-template.py`. Show it on a shot, and say in one line when to use it.
- This skill: the rows in `references/sound-catalog.md`.

## 8. Use it and measure it

Add `"sfx": ["gavel"]` to the shot in `episode.py`, then:

```bash
.venv/bin/python $PROBE gavel --determinism           # PASS; 32% above 250 Hz, 1% below 60 Hz
.venv/bin/python pipeline/build_audio.py episodes/ep02_i_was_right_here --stems
.venv/bin/python pipeline/mixcheck.py episodes/ep02_i_was_right_here
.venv/bin/python pipeline/sound_kit.py                # writes sound_kit/gavel.wav
.venv/bin/python -m pyflakes pipeline/*.py soundtrack.py
```

Result on the scratch copy:
- **Checks:** PASS 5/5.
- **Hit list:** `-23.4 dBFS  peak 41.96 s  basin  +2.57 s  gavel (peak +0.00 s)`. It's the fifth-loudest hit, above both doorbell jumps and below the four reveal and sting hits, landing exactly on its cue.
- **Dialogue:** Mr. Basin's line stayed at 15.3 dB, because the gavel comes after the line, not under it.

Then run the full validation in SKILL.md on every episode. Episodes that don't use the new sound should come out bit-identical: compare `md5sum episodes/*/build/soundtrack.wav` before and after. Adding a generator and a `LEVELS` key changes nothing else, because every sound has its own seed.
