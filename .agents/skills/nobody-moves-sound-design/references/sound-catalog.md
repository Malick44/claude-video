# Sound catalog

Every named sound in the show, where it is made, where the mix puts it and how loud it is. Names are the keys of `soundbank.SYNTH`; the same names are what `soundtrack.py` and an episode's `SOUNDS` can point at a stock file.

## Where each sound comes from and goes

| Name | Generator in `pipeline/sounds.py` | Placed by `build_audio.py` | Bus | `LEVELS` | Kit file |
|---|---|---|---|---|---|
| `theme` | Episodes: `theme_layers(total)`, weighted in `build_audio.py`. `SYNTH`: `motif_bed(sec)` (kit only, see notes) | From the first shot whose `sfx` has `sting` to the end card start + 0.4 s; fades over the last 1.5 s | score | `bed` -17 | `theme_60s` |
| `sting` | `sting(5.0)`: low piano cluster (MIDI 33, 40, 45, 48, 52) + `braam()` + `impact()` | sfx `sting`, at shot start. A `riser` of `min(2.0, start)` s runs into it on `under` | effects | -4 | `sting_title` |
| `sting_end` | `sting(6.0)` | sfx `sting_end`, at shot start | effects | -4 | `sting_end` |
| `sting_soft` | `swell(4.0)`: `PAD_CHORDS[0]` strings rising out of nothing + 55 Hz sub | sfx `sting_soft`, 0.1 s before the shot's last line | score (`under`, ducked) | -11 | `sting_soft` |
| `riser` | `riser(sec)`: noise band 250 to 7000 Hz + rising tones + accelerating tremolo, loudest at its very end | Before every title sting (up to 2 s); across every doorbell flicker (`CTA_DELAY` = 1.9 s) | score (`under`, ducked) | -13 | `riser_2s` |
| `impact` | `impact()`: sub drop + mid body + noise boom + slam + crack + saturated harmonics, in the hall | sfx `shutter` (at `LEVELS["impact"] - 4`); every doorbell reveal at `flicker_at + CTA_DELAY` | effects | -7 | `impact` |
| `braam` | `braam(root=33)`: detuned saw power chord on A1, filter opening on the attack, saturated, plus harmonics | Every doorbell reveal, with the impact | effects | -9 | `braam` |
| `whoosh` | `whoosh()`: 0.9 s noise band 300 to 3200 Hz, panned left to right | 0.45 s before every `qcard` (peaks on the cut) | effects | -17 | `whoosh` |
| `shutter` | `shutter()`: two filtered clicks + flash-charge whine | sfx `shutter`, at shot start, over an impact | effects | -9 | `camera_shutter` |
| `typewriter` | `typewriter_click(i)`: 16 strike variants (`i % 16`); `typewriter_gain(i)` adds -3 to +2 dB per key | One per non-space character of a `qcard`'s `text`, spread over the first 60% of the card from +0.15 s | effects | -20 | `typewriter_key`, `typewriter_question` |
| `ding` | `carriage_ding()`: 2093, 4186, 6280 Hz bell | Just after the typing (0.05 s after its span ends) | effects | -26 | `typewriter_bell` |
| `wind` | `wind(sec)`: noise band-passed 80 to 900 Hz, slow gusts, independent L and R | sfx `wind`, the whole shot; stops dead at the cut | effects | -22 | `wind_20s` |
| `chimes` | `chimes(sec)`: five pitches 1318 to 2349 Hz with partials at x2.76 and x5.4, random strikes, panned | sfx `chimes`, the whole shot; stops dead at the cut | effects | -22 | `wind_chimes_20s` |
| `crickets` | `crickets(sec)`: three crickets at 4.4, 4.75, 5.1 kHz + 60/120 Hz porch-light hum | sfx `crickets`, the whole shot | effects | -25 | `night_crickets_20s` |
| `glitch` | `glitch()`: 880 Hz square buzz in noise | Six times, 0.3 s apart, from each doorbell's `flicker_at` | effects | -22 | `doorbell_glitch` |
| `jump` | `jump()`: the glitch over a short sub hit + harmonics | Each doorbell at `start + doorbell_clock(shot)[1]` (the cut to frame B) | effects | -14 | `doorbell_jump` |

"Every doorbell" includes the replay doorbells that open ep02 and ep03 (`"id": "replay"`, `"kind": "doorbell"`). Each gets the full flicker, riser, reveal hit and score hush. Only the **last** doorbell sets the intensity climax.

## Measured (soundprobe.py, current code)

`0.5s` is the loudest 0.5 s window. `placed` is `0.5s + LEVELS`. For a sound placed alone, it predicts the level mixcheck's hit list shows to within about 1 dB: the title sting reads -14.3 placed and -14.1 in ep02's hit list, and the jump reads -28.2 placed and -27.5. For sounds placed together, power-sum their placed levels, `10*log10(10**(a/10) + 10**(b/10))`: the reveal is impact -16.0 plus braam -17.3, which sums to -13.6 (hit lists: -13.7 to -13.9), and the shutter hit is shutter -32.0 plus the impact at `LEVELS["impact"] - 4`, placed -20.0, which sums to -19.7 (hit list: -19.8).

| Name | sec | 0.5s dBFS | placed | >250 Hz | <60 Hz | L/R |
|---|---|---|---|---|---|---|
| theme (`motif_bed`, 20 s) | 20.0 | -10.7 | -27.7 | 33% | 28% | 0.75 |
| sting | 6.5 | -10.3 | -14.3 | 24% | 17% | 0.78 |
| sting_end | 7.5 | -10.4 | -14.4 | 26% | 22% | 0.77 |
| sting_soft | 7.0 | -9.1 | -20.1 | 7% | 77% | 0.70 |
| riser (2 s) | 2.0 | -14.5 | -27.5 | 100% | 0% | 0.95 |
| impact | 7.0 | -9.0 | -16.0 | 21% | 35% | 0.80 |
| braam | 6.7 | -8.3 | -17.3 | 38% | 5% | 0.86 |
| whoosh | 0.9 | -13.3 | -30.3 | 100% | 0% | 0.91 |
| shutter | 0.25 | -23.0 | -32.0 | 100% | 0% | mono |
| typewriter | 0.06 | -27.5 | -47.5 | 50% | 3% | mono |
| ding | 1.2 | -12.8 | -38.8 | 100% | 0% | mono |
| wind (20 s) | 20.0 | -12.2 | -34.2 | 81% | 0% | 0.01 |
| chimes (20 s) | 20.0 | -10.5 | -32.5 | 100% | 0% | 0.76 |
| crickets (20 s) | 20.0 | -14.7 | -39.7 | 82% | 0% | 0.75 |
| glitch | 0.18 | -21.3 | -43.3 | 100% | 0% | mono |
| jump | 0.6 | -14.2 | -28.2 | 15% | 4% | mono |

The impact and braam carry 13 to 18 dB more `LEVELS` gain than the ambiences on purpose: they are the moments. Placed, they sit 15 to 18 dB above wind and chimes and 22 to 24 dB above crickets. The shutter hit is the impact at -4 (placed -20.0), which is why ep01's shutter shots read -19.8 in its hit list.

## Notes and known quirks

- **`theme` has two versions.** When `theme` is synthesized, `build_audio.py` calls `snd.theme_layers()` and mixes the layers itself: piano 0.85, drone 0.25, pad `0.35 + 0.55 * intensity`, pulse, shimmer. `SYNTH["theme"]` is `motif_bed()`, a fixed-intensity mixdown with different weights, and only `sound_kit.py`'s `theme_60s` uses it. So editing `motif_bed` never changes an episode, and editing the `bed = ...` weights never changes the kit. Mirror a bed change into `motif_bed` if the kit should keep matching. The probe's `theme` row measures `motif_bed`; measure the episodes' score with `soundprobe.py --stems episodes/<ep>`.
- **`sting_soft` is mostly sub.** 77% of its energy is below 60 Hz and 7% above 250 Hz, so a phone speaker plays little more than its string chord. That is fine for a swell under a line. If the user says the board's question lands weakly on a phone, add a harmonics layer (the pattern in "Phone speakers" in SKILL.md).
- **`crickets` peaks at +0.8 dBFS** because the hum is added after `normalize()`. It's harmless: the mix is float and the sound goes in at -25. If you touch `crickets()`, add the hum before normalizing.
- **Ambiences stop dead at the cut.** The synthesized `wind`, `chimes` and `crickets` are generated exactly as long as the shot, with no fade. Ep02's "The wind stopped." relies on that hard stop. A stock ambience goes through `soundbank.fit()` instead, which adds a 0.3 s fade-out.
- **`impact` is used twice.** Replacing or re-leveling it changes both the shutter hit and every reveal hit.
- **Only `LOOPED` names are fit to length** (`theme`, `wind`, `chimes`, `crickets`). A stock `riser` plays at its own length from its start time, so trim the file to peak at its very end and last about 1.9 to 2.0 s, or its peak misses the hit. A stock `typewriter` is one file for every key; the per-key gain jitter still applies.

## Building blocks in `sounds.py`

- **Constants:** `SR` = 48000, `LEVELS`, `THEME_NOTES`, `THEME_TURN`, `THEME_STEP`, `PAD_CHORDS`.
- **Randomness:** `_rng(*key)` gives a numpy Generator seeded from the sha256 of `repr(key)`.
- **Helpers:** `t_axis(sec)`, `midi(n)`, `normalize(y)`, `stereo(y)` (mono to (n, 2)), `pan(y, p)`, zero-phase FFT filters `lowpass(y, fc, order)`, `highpass(...)`, `bandpass(y, lo, hi)`, `saw(freq, t, phase)`, `softclip(y, drive)`, `sweep_noise(dur, f0, f1, width, curve, seed)`.
- **Room:** `reverb(y, seconds, wet)` returns stereo `(n + tail, 2)`: the dry signal centered, plus two decorrelated tails from `_hall(seconds, side)`. `_hall` is `lru_cache`d.
- **Instruments:** `piano_note(freq, dur, vel)` (`lru_cache`d), `_ensemble(notes, t, cents, seed)` (a detuned saw section), `string_pad(total)`, `heartbeat(total, beat)`, `shimmer(total)`, `theme_layers(total)` (a dict of stereo layers `piano`, `pad`, `drone`, `pulse`, `shimmer`), `motif_bed(total, intensity)`.
