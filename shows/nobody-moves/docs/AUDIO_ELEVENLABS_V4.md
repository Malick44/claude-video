# NOBODY MOVES: moving the voices to Eleven v4

Status: decided ([`DECISIONS_EP01R.md`](DECISIONS_EP01R.md), D9 and D10); no voice designed or generated yet. **Decided (D9): the Episode 1 remake (`episodes/ep01r_three_feet_reenacted`) ships with these Eleven v4 voices, and the voice change is tested on its own by re-voicing the Garrison Confessional (`ep05c_garrison_doorbell`) with its visuals unchanged** (in practice a test of Garrison's voice: 7 of its 8 lines are his) (see "Rollout and A/B" and the remake's `TEST_PLAN.md`). Kokoro stays the scratch voice for building before the voice IDs exist. Nothing has been sent to ElevenLabs yet. Anything about v4 that the two ElevenLabs pages below don't state is written as an expectation or marked **to verify**, and gets checked on the first paid run (see "Settings to verify"). The offline code (tag handling, word timing, cache keys, up-front line checks, directions in `SCRIPT.md`) is in the pipeline, tested offline by `pipeline/selftest.py`; "Where each change lands" says what it covers and what is still to do.

Sources, read 2026-10-13:
- ElevenLabs, Models overview: https://elevenlabs.io/docs/overview/models
- ElevenLabs, Eleven v4 announcement: https://elevenlabs.io/blog/eleven-v4

What those pages establish: Eleven v4 was released 2026-09-28. `eleven_v4` is the quality model (10,000 characters per request, 90+ languages, multi-speaker dialogue through the Text to Dialogue API, improved IPA phoneme support, reliable speaker preservation). `eleven_v4_turbo` is the low-latency (~100 ms) variant meant for agents; this show doesn't need it. Delivery is steered with inline audio tags in square brackets (`[laughs]`, `[said angrily in French accent]`, `[light rain]`, `[phone buzzing]`) and natural-language delivery instructions.

What they don't establish: whether `seed` and each `voice_settings` field (`stability`, `similarity_boost`, `style`, `speed`) are honored by v4; whether a voice made with Voice Design renders on `eleven_v4`, and which model Voice Design's previews use; what "reliable speaker preservation" covers (one generation or dialogue, or separate requests); and how v4 takes IPA. Third-party coverage (not ElevenLabs) says SSML `<break>` tags are disabled in v4. Pricing differs between sources, so this document quotes none.

---

## Why

The show's joke is the gap between a prestige true-crime delivery and a flamingo that moved three feet. The edit already owns most of the timing (`P()` pauses, `"music": "out"`, the climax cut). What the voices can't do today is act.

**What Kokoro can't do for this show**
- **No per-line delivery control.** A Kokoro line is shaped by its text and punctuation, the preset (`kokoro_onnx` can also blend presets) and a speaking rate, and that's all. "I didn't see nothing." can't be asked to come out too quickly, "Next question." can't be asked to come out sweetly, and "...I was facing the other way." can't be asked to deflate. Today every button line lands through `P()` and the score drop alone, read in the same prosody as the setup lines.
- **Characters are distinct presets plus pitch shifts.** Each of the eight characters has its own English preset. Garrison (`am_fenrir` at 0.86), Mr. Basin (`bm_lewis` at 0.92) and Ray (`am_puck` at 1.08) are then pitch-shifted with rubberband for age and size, and the chime for its disguise. A shift moves the whole voice, timbre included, and can read as processed rather than as an old gnome or a small frog.
- **Accent is a coin toss between US and GB.** `build_audio.py` picks the accent from the preset's first letter. Lorraine's "hon" and Garrison's "Kid, I've got a perfect view" ask for a regional American voice that no preset has.
- **Kokoro's strength stays:** it's free, offline, deterministic and needs no key. That's why it remains the scratch voice (see Rollout).

**What v4 adds, by the ElevenLabs pages**
- **Timing and deadpan, one line at a time.** Inline tags and natural-language direction let a button line be played differently from its setup: `[too quickly]`, `[quietly]`, `[sweetly]`.
- **Pronunciation.** Improved IPA phoneme support, for names a voice gets wrong (Birchwood, Lorraine, Basin). The pages don't say how v4 takes IPA; check 16 finds out. The `say=` respellings the scripts already use ("nineteen ninety-four", "Mister Basin", "one point six") stay the first fix, because `pipeline/words.py` aligns captions against them.
- **Speaker preservation**, called reliable. The pages don't say whether that holds across separate requests, which is what this show needs: Garrison's 27 lines span 7 folders (6 episodes and 1 Confessional), and each line is its own request. Check 17 measures drift.
- **Later:** 90+ languages make dubbed versions possible. That's out of scope here (`words.py`'s phonemizer is English-only).

**What this plan expects of v4, to verify**
- **A voice from a description.** ElevenLabs' Voice Design makes a voice from a text prompt (age, accent, texture, pace, attitude), which would give each ornament its own voice with no pitch shifting. Neither page says a designed voice renders on `eleven_v4`, or which model the design previews use, so check 0 confirms it before any casting.
- **Restraint with texture.** Deadpan is mostly restraint. The hope is that a designed v4 voice played flat has more texture than Kokoro's default flatness. The public voice test (the re-voiced Garrison Confessional) decides that, not this document.

**What v4 costs the pipeline**, and how this plan covers it: a network call and a key (Kokoro stays as scratch and fallback); money (a cost note below); and determinism. Kokoro reproduces a line exactly. A v4 take may not, and `build/voice/` isn't committed, so a fresh clone would re-generate, re-bill and get a different take. The fix is to keep the take (see "How to lock a take").

---

## Casting

Rules for every Voice Design prompt: describe age, accent, texture, pace and attitude; add "close-miked, dry studio recording" so the hall in `sounds.py` stays the only room; **never** "sounds like <real person>", a named actor, a named narrator or a character an actor is known for. Write each prompt, its preview text, the design date and the resulting `voice_id` into `cast.py` as a comment, for provenance.

**Check 0 comes first.** Design one voice, render its `voice_id` through Text to Speech with `model_id: "eleven_v4"`, and confirm a 200 with `audio/mpeg`. Note which model Voice Design's own previews use. If it isn't v4, judge every candidate voice by a v4 render of the same preview text, never by the preview: a preview on another model (or on `eleven_v4_turbo`) may not match the final render.

**Library voices are a fallback, and never for the narrator.** Third parties upload Voice Library voices, and a search for a narrator voice is the likeliest to return one built to sound like a famous narrator. Reject any Library voice whose name, description, tags or preview names, references or evokes a real person (an actor, a narrator, a public figure) or a known character. Record that check next to the voice's ID and sharing terms in `cast.py`. The narrator is designed only.

**FX default:** designed voices drop the Kokoro-era `pitch` and `speed` (both were workarounds for presets; `speed` is a Kokoro argument, and v4's `voice_settings.speed` is unverified). **The CHIME keeps its chain**, `pitch` plus `"altered": True`, because the documentary "voice altered" sound is the joke ("They altered my voice. Then they added wind chimes." in `ep02c_chime_anonymous`).

| Character | Personality (SERIES.md) | Voice Design prompt | Voice Library fallback searches | FX |
|---|---|---|---|---|
| **NARRATOR** | A serious true-crime narrator. 129 of the season's 239 lines. | A man in his late fifties with a deep, warm baritone and a neutral, educated British accent. Measured but brisk, about 160–170 words a minute, short natural pauses (the edit makes the long ones). Grave and completely sincere, as if every sentence were evidence; never amused, never theatrical, never a trailer voice. Close-miked, dry studio recording. | None: designed only (see above) | None (was pitch 1.0) |
| **GARRISON** | Garden gnome. Gruff and defensive. "Thirty-one years on the lawn." Says he was facing the other way. | A man in his seventies with a low, gravelly, chesty voice and a working-class New York accent. Gruff, clipped and defensive; short sentences, a little impatient, as if he's been asked this before. Medium pace, a slight rasp at the ends of phrases. Close-miked, dry studio recording. | `gruff old man New York`, `gravelly elderly man`, `grumpy grandpa` | Drop pitch 0.86 |
| **LORRAINE** | Concrete porch goose. Warm, unbothered, calls everyone "hon"; when cornered, "hon" becomes "detective". "I don't pick them." | A woman in her sixties with a warm, slightly smoky alto and a light Baltimore-area American accent. Sweet and completely unbothered, a smile in the voice even while she shuts a question down. Medium pace. Close-miked, dry studio recording. | `warm older woman American`, `friendly diner waitress`, `sweet grandmother` | None (was pitch 1.0) |
| **CHIME** | Anonymous source, voice altered. Only talks when it's windy. | An adult of indeterminate age and gender with a soft, breathy, hushed voice, speaking close to the microphone like a nervous informant on a late-night phone call. Light, airy texture, quick and slightly anxious pace, neutral American accent. Dry recording. | `whispering informant`, `breathy hushed voice`, `soft nervous whisper` | **Keep** `"altered": True` and the pitch drop. Start at 0.72; A/B 0.80, since a designed voice may already sit lower than `af_nicole`. The A/B costs nothing: with the patch a pitch change re-runs the FX on the cached clip |
| **MR. BASIN** | Birdbath. Declines to comment; represents himself and anyone else. Has never lost a case, and never had one. | A man in his sixties with a dry, precise, mid-low voice and a formal Received Pronunciation accent from southern England. Slow and careful, as if billing by the word; clipped consonants, pompous but quiet, never raises his voice. Close-miked, dry studio recording. | `posh British lawyer`, `dry elderly British man`, `formal butler` | Drop pitch 0.92 |
| **RAY** | Solar frog. Talks only after a full day of sun, remembers only back to his last full charge. Cheerful once lit. | A man in his early twenties with a bright, light tenor and a friendly General American accent. Cheerful, eager and a little breathless, quick pace, sentences lifting at the end as if everything were good news. Close-miked, dry studio recording. | `cheerful young man`, `upbeat energetic friendly`, `bright tenor` | Drop pitch 1.08 |
| **DALE** | Inflatable Christmas snowman, still up in June. Slow, deflated, unbothered; being flat is his answer to everything. | A man in his forties with a low, soft, airy voice and a relaxed General American accent. Very slow and drawn out, deflated and completely unbothered, long vowels, almost no inflection. Close-miked, dry studio recording. | `slow laid-back man`, `sleepy calm low voice`, `tired deflated` | Drop pitch 0.97 |
| **DEB** | Plastic pink flamingo, the victim. "Condition: unharmed. Position: wrong." Silent for six episodes; first line in Ep. 7: "It's good to be home." | A woman in her fifties with a calm, clear, gently musical voice and a refined, soft British accent. Serene, poised and quietly warm; slow, every word placed as if she had waited a long time to say it. Close-miked, dry studio recording. | `elegant British woman`, `calm mature female narrator`, `serene soothing voice` | None (was pitch 1.0) |

**NARRATOR (TRAILER)**, the remake's one-off speaker for its Director's Cut, is not a separate design: it uses the NARRATOR's `voice_id`, and its one audio tag (`[like a movie trailer]`) makes the change of register, which is the joke. The narrator's own prompt stays "never a trailer voice". If three v4 takes can't land the register (check 18), the line goes to a human (the remake's ★ list).

No prompt asks for breaths. `trim()` keeps anything above -45 dBFS and `speech_map()` counts any frame within 32 dB of the line's peak as voice, so designed-in exhales would sit at clip edges and pull the word highlight around. Dale's `[exhales]` goes on chosen lines only.

For each design, use an in-character preview text of two or three sentences built from the character's own lines (Voice Design asks for preview text; check its current minimum length). Pick the take that's funniest when the line is played straight, not the most expressive one.

**The `cast.py` entries.** These sit in `cast.py` next to `CAST_KOKORO`, the scratch cast. `seed` and `voice_settings` are left out: they go in only under the rules in "Settings to verify". `"lang"` is the accent `words.py` phonemizes in for word timing. `build_audio.phonemizer()` reads it (without it, an ElevenLabs entry is timed as US English) and keeps it out of both cache keys.

```python
# Final voices: ElevenLabs Eleven v4, designed with Voice Design. As a comment beside each voice_id:
# the design date, the full prompt and the preview text (or, for a Library voice, its ID, sharing
# terms and the soundalike check; never for the narrator, who is designed only). seed: added to every
# entry only if the seed check passes, before any take is locked. voice_settings: added per field only
# after it is verified for v4.
PLACEHOLDER = "<fill after design>"
CAST_V4 = {
    "NARRATOR":  {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-gb"},
    "GARRISON":  {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "LORRAINE":  {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "CHIME":     {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us",
                  "pitch": 0.72, "altered": True, "fx_on_recordings": True},   # the disguise is the joke: keep it
    "MR. BASIN": {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-gb"},
    "RAY":       {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "DALE":      {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "DEB":       {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-gb"},
}
FINAL_V4 = set()   # the series default per character, set after the public voice test (Rollout, Phase 4)

VOICES = os.environ.get("NM_VOICES", "")       # anything but "", "kokoro" or "v4" stops with a message
CAST = {**CAST_KOKORO, **{k: CAST_V4[k] for k in FINAL_V4}}   # the decided cast, per character
if VOICES == "kokoro":     # force the free scratch cast for every character
    CAST = dict(CAST_KOKORO)
elif VOICES == "v4":       # A/B builds only: every character on v4
    CAST = {**CAST_KOKORO, **CAST_V4}
```

(An episode's own `CAST` still merges over whichever one is chosen.) The default is decided per character, so a final render with no environment variable ships the decided cast; the variable only forces one side for an A/B. `build_audio.py` stops before voicing anything when a line's character still has the placeholder `voice_id`, naming the shot and line, so a v4 arm is never Kokoro in disguise. `cast.py` also holds `TAGS`, each character's approved tags (next section), as data: nothing reads it until the house-style lint lands.

**The remake ships v4 whatever `FINAL_V4` says.** `episodes/ep01r_three_feet_reenacted/episode.py` holds no voice IDs: it reads `cast.py`'s `CAST_V4`, the same voices the Garrison Confessional's voice test uses, so each character keeps one voice all series. Once its four speakers (NARRATOR, GARRISON, LORRAINE, CHIME) all have a designed `voice_id`, its `CAST` puts them on v4, unless `NM_VOICES=kokoro`; before that it builds on the Kokoro scratch cast. Its one-off NARRATOR (TRAILER) follows: the NARRATOR's v4 entry on v4, the slower, pitched-down `bm_george` preset on Kokoro. With `NM_VOICES=v4` and a placeholder still in place, `build_audio.py` stops at the first line, before voicing anything.

Two cautions on the cast entry:
- **What re-bills.** The patch splits the voice cache in two. The raw clip, and so the API call, is keyed on the generation fields only: provider, `voice_id`, `model`, `seed`, `voice_settings`, and the spoken text with its tags. The processed clip is keyed on the whole entry minus `"lang"`, plus the same text. So the CHIME's pitch A/B (0.72 against 0.80), `altered` and `fx_on_recordings` re-run the FX on the cached raw clip and cost nothing, and `"lang"` changes no key at all. Changing a generation field (a seed, a `voice_settings` value, the model, the voice) or a line's text or tags re-voices and re-bills every line it touches. Settle those before re-voicing, and lock takes (below), keyed on the same generation fields, so a later edit errors instead of spending.
- **Keep non-audio data out of it.** The tag vocabulary (next section) lives in a separate `TAGS` dict, and the Voice Design provenance in comments, so editing either changes no key.

---

## Audio tags house rules for deadpan comedy

**The principle.** Nobody in this show knows it's funny. Tags carry character, never "funny". The narrator stays flat: his gravity is the setup for every joke, and he's 57% of the spoken text. **Untagged is the default.** A tag goes only on a punchline or button line where the delivery makes the joke (the last line of a beat, the denial, the "hon" that turns into "detective"); setups and plants are read straight. It stays only if a blind pick prefers the tagged take over the untagged v4 take of the same line (see "Rollout and A/B").

**When to tag.** Each rule says what the planned house-style lint does about it: *fail* stops the build before any API call, *warn* prints and carries on.
1. **At most one tag per line**, at the start of the line, written in `say` only. *Lint: fail.* The caption (`L`'s second argument) never carries a tag, because it's drawn on screen; the patch's `check_lines()` already stops a build in which a tag would be both shown and sent to the voice.
2. **At most one tagged line per shot, and only on a punchline or button line.** *Lint: fail* on the count; the button rule is the writer's and the reviewer's. It's a ceiling, not a target: most shots have none.
3. **The narrator gets at most one tagged line per episode,** from `[quietly]` or `[gravely]`, and usually none. The doorbell's "Look closer." is the usual candidate. A one-off narrator register such as NARRATOR (TRAILER) is its own speaker and counts separately: at most one tagged line of its own. *Lint: fail.*
4. **Only words from the character's approved list.** *Lint: warn.* The list is house style; a new tag may be right, and it joins `TAGS` once it wins a blind pick.

**Never** (*lint: fail* on each of these tags)
- **Laughter tags** (`[laughs]`, `[chuckles]`, `[giggles]`) on anyone. The moment a witness laughs, the show admits the joke.
- **Sound-effect or ambience tags** (`[light rain]`, `[phone buzzing]`, `[wind]`). They would be baked into the dialogue clip, RMS-matched to -17 dBFS with the voice, would duck the score, and would count as dialogue in `mixcheck`. Sound belongs on the effects bus (`sfx`, `sounds.py`, `soundtrack.py`), where it's deterministic, levelled and measured. The chime's wind stays `"sfx": ["wind", "chimes"]`.
- **Accent tags** (`[in a French accent]`). The accent belongs to the designed voice. A tag that changes it would, we expect, work against keeping a character the same from line to line (not tested).
- **Shouting, screaming or singing.** Deadpan.
- **SSML** (`<break time="1s"/>`). Reportedly disabled in v4 (third-party report); it would either be ignored or read aloud.

**Approved vocabulary** (`TAGS` in `cast.py`)

| Character | Tags |
|---|---|
| NARRATOR | `[quietly]`, `[gravely]` (one line per episode at most) |
| NARRATOR (TRAILER) | `[like a movie trailer]` (provisional: joins `TAGS` only if check 18's takes win the blind pick against the untagged take) |
| GARRISON | `[gruffly]`, `[defensively]`, `[too quickly]`, `[quietly]`, `[under his breath]`, `[with contempt]`, `[flatly]` |
| LORRAINE | `[warmly]`, `[sweetly]`, `[unbothered]`, `[coolly]` (the "detective" turn) |
| CHIME | `[hushed]`, `[nervously]`, `[urgently]`, `[ominously]` |
| MR. BASIN | `[dryly]`, `[formally]`, `[firmly]` ("Objection."), `[clears throat]` |
| RAY | `[cheerfully]`, `[brightly]`, `[excitedly]` |
| DALE | `[slowly]`, `[deflated]`, `[unbothered]`, `[exhales]` |
| DEB | `[serenely]`, `[softly]` (her one line is auditioned untagged first) |

`[clears throat]` and `[exhales]` make a sound before the first word. With the patch, `words.py` times a sound tag as a phrase of its own, so the highlight waits for the pause after the sound and the first word; a direction such as `[quietly]` takes no time. Check 8 confirms where v4 actually puts the sound.

**Pauses, now that SSML breaks are reportedly unavailable**

Pauses come from the edit and from punctuation, never from a pause tag:
1. **Between lines: `P(seconds)`,** exactly as today. It's exact, it's cut to the camera move, and it's free. A pause tag at the start or end of a line does nothing anyway, because `trim()` in `build_audio.py` cuts every clip's leading and trailing silence (below -45 dBFS, with 30 ms of padding).
2. **A beat inside a line: a full stop.** "They just. Stand there." is already the house practice. `words.py` matches each comma or full stop to a pause in the clip, so a pause made by punctuation keeps the word highlight in sync.
3. **Trailing off: an ellipsis** ("So if nobody moves..."). A leading ellipsis stays in the caption only; the `say` drops it and the preceding `P()` makes the beat, as "...I was facing the other way." does today.
4. **A cut-off: an em dash in the caption, and a `say` that simply stops mid-word,** as the chime does today (caption "For the record, I am not a wind—", `say` "For the record I am not a windch"). That respelling was tuned to Kokoro's /wˈɪndtʃ/ (the comment in `ep02c_chime_anonymous` says so), so check 15 tests whether v4 stops dead on it.
5. **A pause longer than about 0.6 s inside a line:** split it into two `L()` items with a `P()` between. The caption splits with it, which is usually right for a button.
6. `[pause]`-style tags: **to verify** on the first run (check 11). If one is used anyway, the patched `words.py` treats `[pause]` and `[beat]` as a phrase break, like a full stop. Prefer the five tools above, which are measurable and survive a re-take.

**The Episode 1 remake's tags, as shipped** (`episodes/ep01r_three_feet_reenacted/episode.py`, D10). Five of its 18 lines, each the punchline or button of its own shot. The NARRATOR has none; NARRATOR (TRAILER) has its one. Tags are in the spoken text only and captions are unchanged. Kokoro, the scratch voice, gets each line without its tag, so the measured timeline doesn't move.

| Shot | Speaker | Caption | Spoken text (`say`) | Why |
|---|---|---|---|---|
| `g_deny` | GARRISON | "I was facing the other way." | `[too quickly] I was facing the other way.` | The alibi, a hair too fast, as if that settles it. The setup ("Kid.") stays untagged |
| `action` | NARRATOR (TRAILER) | "In a world where nobody moves... one goose... dared." | `[like a movie trailer] In a world where nobody moves. One goose. Dared.` | The change of register is the Director's Cut's joke: the narrator's own voice, no pitch shift. Provisional, like its vocabulary row: it stays only if check 18's tagged takes win the blind pick |
| `l_deny` | LORRAINE | "I'm concrete." | `[unbothered] I'm concrete.` | The most obvious fact in the world, gently final, never evasive (on a rewatch she's lying) |
| `chime` | CHIME | "It covers my voice." | `[hushed] It covers my voice.` | It whispers while claiming the wind covers it. "That night? Very windy." is a plant and stays straight |
| `button` | GARRISON | "They made me look short." | `[with contempt] They made me look short.` | He objects to the dramatization, not the accusation |

**Candidates in published episodes** (from `ep01_three_feet/episode.py` and `ep05c_garrison_doorbell/episode.py`; captions unchanged in every case). Lines 7 and 8 go into the Garrison Confessional's voice test (Phase 2); lines 1 to 6 wait for a season re-voice (Phase 4), since the published Episode 1 isn't re-voiced. Each "Candidate" is voiced next to the untagged v4 take of the same line, and kept only if it wins the blind pick. Ep. 1's five candidates sit in five different shots and only one is the narrator's, so all five fit the rules.

| # | Line | Before | Candidate | Why |
|---|---|---|---|---|
| 1 | Ep. 1 `hook_2`, GARRISON, after "I've been standing in this exact spot for thirty-one years." and `P(0.45)` | `L("GARRISON", "I didn't see nothing.")` | `L("GARRISON", "I didn't see nothing.", "[too quickly] I didn't see nothing.")` | The denial comes before anyone asked. The tag carries the hook's button |
| 2 | Ep. 1 `lorraine_3`, LORRAINE, after "Where would I go? I'm concrete." and `P(0.6)` | `L("LORRAINE", "Next question.")` | `L("LORRAINE", "Next question.", "[sweetly] Next question.")` | Warm while shutting the door: her whole character in two words |
| 3 | Ep. 1 `garrison2_2`, GARRISON, after "Kid, I've got a perfect view of that lawn. Twenty-four hours a day." | `P(0.8)`, `L("GARRISON", "...I was facing the other way.", "I was facing the other way.")` | `P(0.8)` kept, `L("GARRISON", "...I was facing the other way.", "[quietly] I was facing the other way.")` | The edit makes the beat; the tag makes the deflation. The setup line stays untagged so the drop has somewhere to fall from |
| 4 | Ep. 1 `chime_2`, CHIME | `L("CHIME", "They just... stand there.", "They just. Stand there.")` | Unchanged | The pause is a full stop, already the house rule. No `<break>`, no `[pause]`. The designed voice is hushed without a tag |
| 5 | Ep. 1 `chime_5`, CHIME, the beat's last line, after `P(0.55)` | `L("CHIME", "It was very windy.")` | `L("CHIME", "It was very windy.", "[ominously] It was very windy.")` | A wind chime treating wind as a dark revelation. Lines `chime_1` to `chime_4` stay untagged |
| 6 | Ep. 1 `board_3` and `doorbell_2`, NARRATOR | `L("NARRATOR", "who moved Deb?")` ... `L("NARRATOR", "Look closer.")` | `board_3` unchanged (no `[dramatically]`); `L("NARRATOR", "Look closer.", "[quietly] Look closer.")` | The board line is the title question: flat is funnier. The narrator's one tag of the episode, if any, goes on the doorbell, where it reads as dread |
| 7 | Ep. 5c `hook_2`, GARRISON, after "That doorbell across the street?" and `P(0.25)` | `L("GARRISON", "Nosy.")` | `L("GARRISON", "Nosy.", "[with contempt] Nosy.")` | A one-word hook needs a reading, and the grudge has to land inside two seconds |
| 8 | Ep. 5c `punch_1`, GARRISON, the climax: `P(0.7)`, music out | `L("GARRISON", "...I was facing the other way.", "I was facing the other way.")` | `L("GARRISON", "...I was facing the other way.", "[flatly] I was facing the other way.")`, `P(0.7)` and `"music": "out"` kept | Third time he's used the alibi, so he says it like a rehearsed statement. It contrasts with the remake's `[too quickly]` (and with Ep. 1's `[quietly]` candidate): the callback changes delivery, not words |

Unchanged on purpose: `specs_1`'s respelling ("Takes my picture every one point six seconds.") and Ep. 1's `basin_1` "Mister Basin" (the remake has no Mr. Basin line). v4 may read "1.6" and "Mr." correctly, but the respelling is deterministic and is the text `words.py` aligns. The narrator's `specs_5`, "How do you know all that?", stays flat: it's the setup for line 8.

---

## Dialogue

**Recommendation: voice every line on its own with the Text to Speech endpoint, as the pipeline does today. Use Text to Dialogue only to audition an exchange, never as production audio.**

Why per-line clips:
1. **The edit owns timing.** Every gap between lines is a `P()` cut to a camera move, and the biggest laughs sit on those gaps (Ep. 5c's `P(0.7)` into "...I was facing the other way." with the score cut). A dialogue render bakes its own gaps in.
2. **Captions.** `words.py` measures each finished clip against that line's `say`; `timeline.json` stores one caption per line with its own word timings. A multi-speaker clip would first need splitting by speaker, which this pipeline has no tool for. Whether Text to Dialogue returns per-speaker timings isn't confirmed on the ElevenLabs pages read.
3. **Per-line processing.** Each line is RMS-matched to -17 dBFS, and the CHIME's pitch and "altered" chain runs on its lines only. Neither works on a clip that mixes speakers.
4. **Per-line overrides and cache.** A user recording (`recordings/<shot>_<n>.m4a`) replaces one line, and an edited line re-voices (and re-bills) one line, not the whole exchange.
5. **The format rarely needs it.** The show is interviews: mostly one speaker per shot, separated by question cards. Its few exchanges are two or three lines inside one shot with a measured `P()` between them (Ep. 3: "Objection." `P(0.6)` "There is no judge."), and that `P()` is the joke's timing. Nobody interrupts or overlaps anyone.

Where Text to Dialogue helps: an exchange whose reactive rhythm is hard to guess (Mr. Basin and the narrator in Ep. 6: "My client has no comment." / "He isn't your client." / "Then he has no counsel. And no comment."). Render it once through Text to Dialogue as a reference, measure its gaps, and copy them into the `P()` values; then voice the lines one by one with the same voice IDs. Revisit only if ElevenLabs documents per-speaker timings for dialogue output and a beat genuinely needs overlap.

Continuity across separate requests is what this show needs from "reliable speaker preservation", and the pages don't say the feature covers it; check 17 measures it. The TTS API has had request-stitching inputs (`previous_text` / `next_text`) for earlier models; whether v4 honors them is **to verify** (check 14).

---

## Settings to verify on the first run

Everything here is unconfirmed for v4 by ElevenLabs. Run check 0 before designing the cast, and the rest once, on one voice and one line each (unless the row says otherwise), before re-voicing any episode; fill the Result column. Measure each outcome with numbers (durations, the sha1 of the mp3 bytes, the pauses `words.speech_map()` finds, RMS); then listen. Budget roughly 2,000 to 3,000 characters for the whole matrix, plus the Voice Design previews.

| # | Check | How | Pass | Result |
|---|---|---|---|---|
| 0 | Voice Design on v4 | Design one voice. Render its `voice_id` through Text to Speech with `model_id: "eleven_v4"`; note which model Voice Design's previews use | 200 with `audio/mpeg` from the v4 render. If the previews aren't v4, candidates are judged by v4 renders only | |
| 1 | Model accepted | POST `model_id: "eleven_v4"`, plain text, today's `output_format=mp3_44100_128` | 200 with `audio/mpeg` | |
| 2 | `seed` honored | Same voice, text and seed, 3 times; then a different seed | **Pass:** the same seed gives identical mp3 bytes (same sha1) or identical decoded PCM, **or** is near (duration within 1% and `speech_map()` finds the same number of pauses) while the different seed is not near. Anything else fails | |
| 3 | `seed` rejected | Check 2's status codes | A 4xx fails check 2 | |
| 4 | `stability` | 0.0, 0.5, 1.0, two takes each | Take-to-take spread changes with the value; otherwise "ignored" | |
| 5 | `similarity_boost`, `style` | Two values each | Audible difference by ear; no measure is reliable | |
| 6 | `speed` | 0.8, 1.0, 1.2 inside `voice_settings` | Duration scales roughly with the value | |
| 7 | Tags aren't spoken | "[quietly] Look closer." against "Look closer." | Same word count by ear; the tagged clip isn't longer by a spoken word | |
| 8 | Non-verbal tags | "[exhales] Flat." | Where the sound sits; how long before the first word, and whether a pause follows it (the patched `words.py` expects one) | |
| 9 | SSML | `They just. <break time="1.0s"/> Stand there.` | Confirms or refutes the third-party report: pause, ignored, or read aloud | |
| 10 | Punctuation pauses | "They just. Stand there." / "They just... stand there." / "They just — stand there." | The pause lengths `speech_map()` finds; pick the house mark per beat length | |
| 11 | Pause tags | "They just [pause] stand there." | Whether a pause appears, and how long | |
| 12 | Numbers | "1.6", "3:12 AM", "1994" raw against the respelled `say` | Keep respellings regardless; note v4's behavior | |
| 13 | Word timestamps | The `with-timestamps` TTS variant, if it accepts `eleven_v4` | If it does, its alignment could replace `words.py`'s estimate for ElevenLabs lines (strip tag characters first) | |
| 14 | Request stitching | `previous_text` / `next_text` with v4 | Accepted or rejected | |
| 15 | A cut-off | The CHIME voice reads "For the record I am not a windch" | The clip stops on /tʃ/ without finishing "chime" or spelling letters; if not, find a v4 respelling | |
| 16 | IPA | How v4 takes IPA for "Birchwood": inline markup (SSML `<phoneme>`, which may be disabled along with `<break>`), a pronunciation dictionary, or neither | Note the mechanism. A respelling in `say` stays the first fix. If IPA is inline markup, strip it before word timing the way tags are stripped, and add it to the lint | |
| 17 | Drift across requests | The GARRISON voice reads 5 of his lines from 5 different folders, one request each | Median pitch within a semitone and seconds per character within 10% across the five, and no drift by ear | |
| 18 | A register tag | The NARRATOR voice reads the remake's `action_1` with and without `[like a movie trailer]`, three takes each | The tagged takes are audibly lower, slower and bigger in the same voice, with no tag spoken and no shouting, and the tagged take beats the untagged one in the blind pick (otherwise the provisional tag is dropped). Record each take's length: every take's growth over Kokoro comes out of one shared budget, the remake's headroom (3.1 s; a 5.15 s take, `action` at `dur` 6.0, would use 1.35 s of it). Lock this take before `rx_action_goose` is generated, since the clip is fitted to it; once a clip exists it absorbs a take of up to about 4.0 s, and over that the clip is regenerated as a 10 s take with the landing re-timed (raising `dur` alone freezes it and lands her before "dared"). If no take lands the register, the line goes to a human (the remake's ★ list) | |

**One rule for each unverified field.** `seed` goes into the cast entries only if check 2 passes, and that's decided in Phase 1, before any take is locked: adding or removing it later changes every line's generation key and re-bills. Each `voice_settings` field goes in only if its check (4 to 6) shows an effect. Nothing unverified is sent on faith.

### How to lock a take

v4 isn't guaranteed to repeat itself, and `build/` isn't committed. Treat a chosen take like a stock asset: fetched once, kept, pinned.

1. **The cache isn't a lock.** `build/voice/<WHO>_<key>.wav` survives rebuilds on one machine only. A fresh clone, a deleted `build/` or an edit to a generation field re-generates, re-bills and gets a different take.
2. **The seed narrows retakes, if check 2 passes.** It never replaces keeping the file: a model update can change the output for the same seed.
3. **Keep the mp3.** Today `voice_line()` decodes the API's mp3 straight to a 24 kHz WAV and discards it. Proposed: save the bytes verbatim as `episodes/<ep>/takes/<rec>.mp3` and record each in `episodes/<ep>/takes/takes.json`, the way `stock/sources.lock.json` pins fetched sounds: `rec`, `who`, `voice_id`, `model`, `seed`, `voice_settings`, the exact text sent (tags included), the generation key (the raw clip's key from the patch), the date, and "take 2 of 3". Commit `takes/`; at 128 kbps an episode's dialogue is under a megabyte.
4. **Source order becomes:** `recordings/<rec>.*` (the user's own take), then `takes/<rec>.mp3` when its generation key matches the current cast entry and `say`, then the API. An FX or `"lang"` edit doesn't change that key, so it never stales a take. When the key doesn't match (the line, its tags or a generation field changed), the build **stops** with "take for `<rec>` is stale; re-voice with `--revoice <rec>`" instead of spending silently.
5. **Choosing among candidates:** `build_audio.py --candidates 3 --only <rec>` writes `takes/candidates/<rec>.{1,2,3}.mp3`, and a small `tools/takes.py pick <rec> 2` promotes one. Button lines usually deserve three candidates; setup lines, one.
6. **Zero-code fallback, usable today:** build, then copy the line's raw clip, `build/voice/<WHO>_<key>_raw.wav`, to `recordings/<rec>.v4.wav`. To find it, take the newest raw file right after building that line (`ls -t build/voice/<WHO>_*_raw.wav | head -1`), or compute the key: with the patch it's `sha1(json.dumps([entry, say]))[:12]`, where `entry` is the cast entry without `pitch`, `altered`, `fx_on_recordings` and `lang`, and `say` is the spoken text with its tags (without the patch, the whole entry). For another candidate, move that line's `<WHO>_<key>*.wav` files out of `build/voice/` and build again; each one is a new paid request. The build then uses the copy in place of the API (after the user's own take, `recordings/<rec>.<ext>`, which wins), and `timeline.json` marks the line `"generated"`, so the end card still names the voices and `SCRIPT.md` counts it as a locked v4 take, not a human recording. `NM_VOICES=kokoro` skips `.v4` takes, so a Kokoro build stays Kokoro after locking. The CHIME's entries in both casts carry `"fx_on_recordings": True`, so its disguise runs on the take. Downsides: the take is already down to 24 kHz (the API's mp3 is gone), and the voice credit (the `voice_id` and model) disappears from `SCRIPT.md`'s Voices table. A take copied without the `.v4` (`recordings/<rec>.wav`) counts as a human take: it wins over every cast, Kokoro included, and on an episode without a reenactment the end card drops "voices" ("Reenactments dramatized with AI."). Before posting such an episode, check `render.py --preview <end start + 1.9>` reads "Reenactments and voices made with AI."

Also worth measuring: the voice cache runs at `VOICE_SR = 24000` (Kokoro's native rate), so a 44.1 kHz ElevenLabs take loses everything above 12 kHz before the 48 kHz mix. Phone speakers won't show it; headphones may. Caching ElevenLabs clips at their native rate is a small change in `voice_line()` and `trim()`.

---

## Consent & disclosure

- **No cloning of real people.** Every voice in this cast is designed from a text prompt (or, as a fallback for characters other than the narrator, taken from the Voice Library). Nobody's recordings are uploaded: not an actor's, a narrator's, a public figure's or a friend's. The only exception the show could ever make is the creator's own voice, through ElevenLabs' own verification flow, disclosed the same way.
- **No imitation by prompt.** A Voice Design prompt never names a real person, a named narrator, or a character an actor is known for. Each prompt is stored next to its `voice_id` in `cast.py`, so the provenance can be checked.
- **No imitation by Library pick.** Reject any Library voice whose name, description, tags or preview names, references or evokes a real person or a known character, and record that check in `cast.py` next to the voice's ID and its sharing terms. Check the sharing terms on the voice's Library page before using it commercially. Prefer a designed voice saved to the show's own account, which a third party can't withdraw from under the series; the narrator is always designed.
- **End card.** `render.py` draws "Reenactments dramatized with AI." / "The flamingo is real." With the reenactment shot kind it widens the first line:
  - on any episode with a reenactment, **"Footage, reenactments and voices made with AI."** whatever the cast. Its photoreal stills and doorbell frames are AI images too, and once reenactment frames say "· AI" and the doorbell says "NOT A REENACTMENT", a first line that named only reenactments and voices would teach viewers that unlabelled means real. The Episode 1 remake uses it from its first post (689 px at 30 px, inside the 780 px `render.py` gives the NEXT line);
  - on an episode without a reenactment whose soundtrack holds an ElevenLabs voice (a line voiced by one, or a locked v4 take; `build_audio.py` records which in `timeline.json`, so the card follows the build whatever `NM_VOICES` says when `render.py` runs), **"Reenactments and voices made with AI."** (565 px), at the card's usual timing. The re-voiced Garrison Confessional is the first;
  - every other episode is unchanged, so the published ones stay byte-identical.

  Still two lines, so no layout change; re-run `pipeline/safezones.py` anyway. The flamingo line stays last, because it's the joke.
- **Platform labels.** The YouTube "altered or synthetic content" answer stays **yes** on every Short (`channel/CHANNEL.md` already requires it); with voices this realistic it's no longer a formality. TikTok's AI-generated label and Instagram's "AI info" stay on. The description line follows the end card: "Written by [NAME]. Footage, reenactments and voices made with AI. The flamingo is real." on an episode with a reenactment (the remake), and "Written by [NAME]. Reenactments and voices made with AI. The flamingo is real." on a re-voiced episode without one (the Confessional).
- **Attribution:** check whether the account's plan requires crediting ElevenLabs, and if so, add it to the description and to `SCRIPT.md`'s credits (which already list `ElevenLabs <voice_id>` per character, and with the patch its model too).

---

## Rollout and A/B

**Decided (D9):** the Episode 1 remake ships with v4 voices, so its A/B against the published Episode 1 changes picture and voice together. The voice is isolated in a test of its own: the Garrison Confessional re-voiced on v4, visuals unchanged, against the published one. Kokoro stays the scratch voice: every episode builds on it before its voice IDs exist (`NM_VOICES=kokoro` forces it), it costs nothing, and its build is the reference `review.py --ref` compares against.

**Phase 0, offline (no key).** Done for tags, word timing, cache keys, line checks and directions (the v4 tags patch, now in `pipeline/`, `cast.py` and `README.md`), with `pipeline/selftest.py`'s mock extended to `eleven_v4`. With real Kokoro, `ep02c_chime_anonymous` builds byte-identical before and after the patch (`timeline.json`, `soundtrack.wav`, `SCRIPT.md` and the processed voice clips; only the raw clips of pitched voices get new names, from their generation key), and the same episode with tags on every line reuses that cache and builds the same soundtrack. The remake's five tagged lines pass `check_lines()` on the Kokoro scratch cast and on a v4 cast. `CAST_V4`, `FINAL_V4`, `TAGS` and the `NM_VOICES` switch are in `cast.py`. Still to write: the house-style lint and the takes lock ("Where each change lands").

**Phase 1, design.** Run check 0, then design the four voices the remake and the Garrison Confessional need (NARRATOR, GARRISON, LORRAINE, CHIME; NARRATOR (TRAILER) uses the NARRATOR's ID). Run the rest of the matrix on the narrator, check 15 on the CHIME, check 17 on GARRISON and check 18 on the trailer line. Decide `seed` here. Fill the four `voice_id`s in `cast.py`'s `CAST_V4`; the remake and the Confessional both read them from there.

**Phase 2, voice the two test videos and lock their takes.**
- **The remake** (`ep01r_three_feet_reenacted`, 18 lines, 5 speakers, 5 tagged lines). Each line gets up to 3 v4 takes; setup lines usually need one. A tagged line's takes are picked blind against one untagged v4 take of the same line, and the tag is dropped if the untagged take wins. **A line that no take lands in 3 tries goes to a human:** the five ★ lines in its `SCRIPT.md` ("Lines to record by a human") are the likeliest, each with its direction and same-session companions. **Voice and lock `heist_1` and `action_1` first, before their clips are generated:** each clip is fitted to its take (`NOTES.md`, length rule). Among takes that land a line, prefer the one closest to Kokoro's length, and record each take's words/min. Then re-run the timeline on the locked takes: under 50 s (46.9 s on Kokoro, so all the takes together may grow by 3.1 s), about 165 words/min while speaking (150 the floor) and 110–120 overall. Over 49.5 s, apply the remake's trim list (`NOTES.md`, "Pace"). A longer line on a reenactment raises that shot's `dur` (at most 6.0 s) and sets its clip's hold time.
- **The Garrison Confessional** (`ep05c_garrison_doorbell`, 8 lines), re-voiced on v4 with its candidates 7 and 8 picked the same way. Its stills, edit, captions and music are unchanged; only the voices, and the timing that follows from their takes, differ from the published video.
- Candidate takes come from `build_audio.py --candidates 3 --only <rec>` once the takes lock lands; until then, from the zero-code fallback in "How to lock a take". Lock every chosen take before the final render.
- **Run the Kokoro arm, or copy the Kokoro build's `build/timeline.json` aside, before locking any take.** It is the reference `fit_takes.py --ref` and the gate's +5% rule (D1) measure against. A locked `.v4` take is skipped under `NM_VOICES=kokoro`, but a recording wins over every cast: a take copied without `.v4`, or a human take, makes `NM_VOICES=kokoro` no longer Kokoro for that line. To rebuild the Kokoro reference later, move those takes out of `recordings/` first.

```bash
cd shows/nobody-moves; PY=.venv/bin/python; AB=$HOME/nobody-moves-ab   # outside the repo
arm() {   # arm <name> <NM_VOICES> <episode>: full build, stems, mixcheck, safe zones, then a copy of build/
  NM_VOICES=$2 ./make_episode.sh episodes/$3                       # the timeline changes: full render, not a remux
  NM_VOICES=$2 $PY pipeline/build_audio.py episodes/$3 --stems
  mkdir -p $AB/$1/$3 && $PY pipeline/mixcheck.py episodes/$3 --json > $AB/$1/$3/mix.json
  NM_VOICES=$2 $PY pipeline/safezones.py episodes/$3                # needs episode.py: run it here, not on the copy
  rm -rf $AB/$1/$3/build && cp -r episodes/$3/build $AB/$1/$3/build    # no nesting on a re-run
}
# The Confessional's candidates 7 and 8 go into its episode.py first; the remake's tags are already in.
EPS="ep05c_garrison_doorbell ep01r_three_feet_reenacted"
# Under NM_VOICES=v4, build_audio.py stops before voicing while a voice_id in cast.py is a placeholder.
for ep in $EPS; do arm kokoro kokoro $ep; arm v4 v4 $ep; done       # v4 last: the remake's SCRIPT.md is the v4 one
git checkout -- episodes/ep05c_garrison_doorbell/SCRIPT.md            # keep the published Confessional's script
for ep in $EPS; do $PY pipeline/review.py $AB/v4/$ep --ref $AB/kokoro/$ep --no-zones; done   # the copies hold only build/
```

`review.py --no-zones` reads only `<dir>/build/timeline.json` and `<dir>/build/<basename of dir>_tiktok.mp4`, which is why each copy sits at `$AB/<arm>/<episode>/build`. Its safe-zones step loads the episode itself (`episode.py`, stills, clips), which a build-only copy doesn't hold, so `arm()` runs `safezones.py` on the episode before copying, and `build/review/zones.png` travels with the copy. Run the arms before locking any take ("Phase 2" above). The Kokoro arm rebuilds from cache and costs nothing; switching back and forth is free after the first v4 build, because the cache keys differ. The Confessional's tag candidates stay in its `episode.py` until the pick; then the losers are removed and it is rebuilt.

**Blind picks** (internal, before posting). They choose takes and tags; whether the remake ships v4 is already decided. Three to five raters, each scoring 1 to 5 on "in character", "funny" and "clear", on a phone speaker and then on headphones.
- **Takes and tags, per line:** the line cut from each candidate build (its `start` and `end` in `timeline.json`, plus a second either side), played in random order, with the untagged take among them for a tagged line.
- **Length:** among takes that land the line, prefer the one closest to Kokoro's length, and record each take's words/min. The remake's runtime budget is shared by every take (`episodes/ep01r_three_feet_reenacted/NOTES.md`, "Pace"); its `tools/fit_takes.py --ref <the Kokoro build's timeline.json>` names any take more than 5% longer than Kokoro's.
- **Voice, per character (an internal gate before posting, not the public test):** the Kokoro and v4 builds, renamed A and B at random: the Confessional's `_tiktok.mp4` files for GARRISON and the NARRATOR, and the remake's lines for LORRAINE, the CHIME and the trailer register. A v4 voice that scores more than 0.5 lower on "in character" is redesigned (back to Phase 1) before anything is posted. This is also the only check LORRAINE and the CHIME get before `FINAL_V4`: the public voice test can't speak for them (see "Decision").

**What to listen for**
- **Deadpan:** the narrator never smiles, swells or "trailers". If v4 makes him sound like he's in on it, the show breaks. The one exception is the remake's NARRATOR (TRAILER) line, where the trailer register is the joke.
- **Buttons:** for each tagged line, does the tagged take beat the untagged one? Garrison's alibi is `[too quickly]` in the remake and the Confessional's candidate is `[flatly]`; if both win, is the contrast audible? The callback changes delivery, not words.
- **The trailer line:** does `[like a movie trailer]` change the register while the voice stays the narrator's?
- **Separation:** are all four voices distinguishable on one phone speaker, with no pitch shifting?
- **The chime:** is it still obviously "voice altered" with the designed voice, and does "They altered my voice" still land? A/B pitch 0.72 against 0.80 (free: only the FX re-runs).
- **Quiet tags:** every clip is RMS-matched to -17 dBFS, so `[quietly]`, `[hushed]`, `[softly]` and `[under his breath]` come back at normal loudness with their breath and noise turned up too; only the timbre survives. Are those lines still intelligible on a phone speaker, and do they still read as quiet? If the level difference matters, add an optional per-line gain to `L()` in `build_audio.py` rather than relying on the tag.
- **Lorraine's turn** (Eps. 3 and 5, in Phase 4): with `[coolly]`, does "detective" read as the switch from "hon"?
- **Pronunciation:** Birchwood, Lorraine, Mister Basin, nineteen ninety-four, three twelve, one point six.
- **Fidelity to the text:** every word in `say`, no extra words, no audible tags, no breaths or clicks at clip edges.
- **Caption sync:** the yellow word stays on the voice on tagged lines (`render.py --preview` at a tagged line's word times), and doesn't light up during a sound tag.

**What to measure**
- `mixcheck`: loudness, dialogue over bed (median ≥ 12 dB, aim for 15+, nothing under 8), the worst lines, phone presence. Compare the arms against each other and against `.agents/skills/nobody-moves-sound-design/references/baselines.md`.
- The CHIME's own dialogue-over-bed lines: a breathy, hushed design, pitched to 0.72 and bit-crushed under wind and chime ambience, is the likeliest to hit mixcheck's 8 dB warning.
- The loudness and intelligibility of every quiet-tagged line (above).
- `review.py --ref` between the arms for beat timing.
- Runtime: per-shot durations from `timeline.json`, and each take's words/min. The remake must stay under 50 s (D7): it is 46.9 s on Kokoro (167 words/min while speaking, 111 overall). At about 150 words/min it would run 50.4 s, 0.4 s over the ceiling, at 104 words/min overall: D1's overall target and D2's headroom hold on v4 only if the takes average about 164 words/min or faster while speaking (159 for the headroom alone). So D1's final target is ~165 words/min while speaking, with each take no longer than its Kokoro take +5%; that's why the casting prompts ask for a brisk narrator and no slow pace. TikTok's 60 s Creator Rewards minimum is revisited near eligibility, not in this test.

**Phase 3, the public tests.** The remake's `TEST_PLAN.md` has the arms, metrics, thresholds and order:
1. **The voice test first:** the re-voiced Garrison Confessional against the published one. Only the voices changed, and 7 of its 8 lines are Garrison's (the narrator has one 25-character line), so a difference is **Garrison's v4 voice** with its house-rule tags. LORRAINE, the CHIME, the trailer register and 4 of the remake's 5 tags never appear in it.
2. **The package test, at least 7 days later:** the remake (3D reenactments, the remake's structure and v4 voices) against the published Episode 1. Picture and voice change together, so it can't credit either one alone; read it next to the voice test.

**Decision.** The remake ships v4 either way (D9). The series default (`FINAL_V4`) follows the voice test, which speaks for Garrison's voice only:
- **Voice wins** (B2 beats A2 by more than the margin; `TEST_PLAN.md`, "Voice test"): GARRISON goes into `FINAL_V4` once his episodes pass mixcheck. The NARRATOR, LORRAINE and the CHIME go in only after passing the internal per-character check ("Blind picks": not more than 0.5 below Kokoro on "in character", and "clear" on a phone speaker), and the record states that they were not tested in public. Phase 4 can then start.
- **Voice loses:** B2 is below both A2 and the median of the other five Confessionals by more than the margin. New episodes stay on Kokoro, and the voices are redesigned before another try.
- **Flat** (B2 between those) **or inconclusive** (under 50 feed impressions): keep Kokoro for new episodes, and read the package test as the whole package only.
- **The package's follow-ups.** "New episodes" above means episodes outside the reenactment test. The Episode 2 remake belongs to the reenactment package and uses the remake's v4 voices whatever the voice test says; if the voices are redesigned, re-voice the remake with them before the Episode 2 remake. The replication Confessional is voiced to match its baseline: on v4, judged against B2, if the voice test won; otherwise on Kokoro, judged against A2 (`TEST_PLAN.md`, criterion 5).
- **With the package test:** a voice loss plus a flat or lost package test says nothing about the format, because B carried a voice already shown to lose. The replication Confessional, voiced on Kokoro, decides the format instead (`TEST_PLAN.md`, "Reading the two together").

A tag stays when its tagged take wins the blind pick against the untagged v4 take of the same line: from 3 or more raters, a mean at least 0.5 higher on "in character" and on "funny", and not lower on "clear". Anything less goes back to untagged, the default.

**Phase 4, the season** (only after the voice test converts): design the remaining four voices (MR. BASIN, RAY, DALE, DEB) and re-voice all 13 folders in one pass, so the season is consistent; new tag candidates (lines 1 to 6 above among them) go through the same pick. Lock every take before the final render. Already-posted episodes won't match the new ones; decide whether the re-voice replaces Season 1 or the switch starts with the next new episodes (Season 3). Season 2's seven published episodes are not in the repo or in the 13-folder count, and stay as posted.

**Cost note (no prices).** Spoken characters per folder, counted from each `L()`'s `say` (the caption when `say` is absent), before tags:

| Scope | Lines | Characters |
|---|---|---|
| Ep. 1 remake, "Three Feet, Reenacted" | 18 | 456 (NARRATOR 248, CHIME 70, GARRISON 55, NARRATOR (TRAILER) 48, LORRAINE 35); its five tags add 75 |
| Ep. 1, "Three Feet" (published) | 24 | 833 (NARRATOR 467, GARRISON 174, CHIME 129, LORRAINE 63) |
| Ep. 5c, Garrison Confessional | 8 | 193 (GARRISON 168, NARRATOR 25); candidates 7 and 8 add 25 |
| All 13 published folders (7 episodes, 6 Confessionals) | 239 | 6,722 (NARRATOR 3,856, GARRISON 871, LORRAINE 774, MR. BASIN 428, CHIME 380, DALE 220, RAY 172, DEB 21) |

- **Phase 2** bills the remake and the Confessional. One full take is about 530 characters for the remake (456 spoken plus 75 of tags) and about 220 for the Confessional (193 plus 25), plus one untagged reference take of each tagged line (about 130 and 30).
- **Tags** add about 16% to the remake (five tags on a short episode, the trailer tag the longest) and about 13% to the Confessional. A longer episode stays nearer Ep. 1's 7% (its five candidates add 56 characters). Assume tags are billed as characters: unverified.
- **Retakes multiply:** billed ≈ (spoken + tags) × average takes per line, plus the untagged references. At two takes on average, that's about 1,200 characters for the remake, about 470 for the Confessional, and about 14,400 for a whole-season re-voice (Phase 4).
- **Also budget** the settings matrix (about 2,000 to 3,000), the Voice Design previews, and any generation-field edit made before takes are locked: that edit re-bills every line of the character. FX and `"lang"` edits cost nothing.
- Check the account's plan quota against these numbers; this document quotes no price.

---

## Where each change lands

"In the patch" marks the offline code of the v4 tags patch, merged with the Episode 1 remake; "Done" was built with the remake's reenactment code; "To do" is still to build. Each rule goes into the shared workflow, not into one episode.

| Change | File | Status |
|---|---|---|
| Tags reach ElevenLabs as written and Kokoro without them (`voiced_text()`); the word timing uses the text the voice got; `"lang"` read by `phonemizer()`; the raw clip keyed on generation fields only, so FX and `"lang"` edits don't re-voice or re-bill; each caption's tags kept in `timeline.json` | `pipeline/build_audio.py` | In the patch |
| Up-front line checks (`check_lines()`, before any API call). Fail: a tag that would be both on screen and sent to the voice, a bracket in the spoken text that isn't a whole tag, a Kokoro line that is only tags, a speaker missing from the cast, an ElevenLabs voice whose `voice_id` is still the placeholder. Warn, once per character: tags on a Kokoro voice, or on an ElevenLabs model outside `TAG_MODELS`. Recorded lines are skipped | `pipeline/build_audio.py` | In the patch |
| House-style lint in `check_lines()`. Fail: more than one tag per line, a tag not at the start, more than one tagged line per shot, more than one NARRATOR tag per episode (a one-off register such as NARRATOR (TRAILER) counted on its own), laughter, sound-effect or accent tags, `<break`, IPA markup if check 16 finds it is markup. Warn: a tag outside the character's `TAGS`, and a tag on a line that isn't its shot's last (a button usually is). Until it lands, the write skill's checklist applies these rules by hand, against the vocabulary table in this file | `pipeline/build_audio.py` | To do |
| Word timing: a direction takes no time, a pause tag ends a phrase, a sound tag (`[exhales]`, `[clears throat]`, `[sighs]`) is timed as a phrase of its own (`tag_kind()`, `spoken_units()`); `strip_tags()` leaves no stray space or token by quotes or dashes; self-check cases with a noise burst where the sound is | `pipeline/words.py` | In the patch |
| The takes lock (`takes/`, `takes.json` keyed on the generation key, `--revoice`, `--candidates`, the stale-take error); keep the raw mp3; optional native-rate cache for ElevenLabs | `pipeline/build_audio.py` | To do |
| `TTS_MODEL` and `TAG_MODELS` constants | `pipeline/stock.py` | In the patch |
| Return the response bytes and headers so a take can be stored as sent | `pipeline/stock.py` `elevenlabs_tts()` | To do |
| Mock: text-to-speech for known voice ids only (404 otherwise), a trailing `[yawns]` rendered as a sound. Checks: tags reach the request body and never the captions; the sound gets no highlighted word; Kokoro gets no tags (stubbed `create()`); a tag-only edit re-voices an ElevenLabs line; FX and `"lang"` edits don't call the API; every `check_lines()` outcome; bad lines stop before any clip is written | `pipeline/selftest.py` | In the patch |
| Mock and checks: a locked take skips the API; a stale take stops the build | `pipeline/selftest.py` | To do |
| Voice provenance in `timeline.json`: an ElevenLabs line carries `"provider"`, `"voice_id"` and `"model"`, a locked `recordings/<rec>.v4.*` take `"generated"` (and `NM_VOICES=kokoro` skips it); the end card and `SCRIPT.md`'s Voices table read them instead of the cast in force when they run. Checked by `selftest.py` (built with `NM_VOICES=v4`, the end card rendered without it; a locked take keeps "voices", a human take drops it) | `pipeline/build_audio.py`, `pipeline/render.py`, `pipeline/script_md.py` | Done |
| A line's tags as an italic direction after it, *(too quickly)*, so someone recording it sees the delivery; the ElevenLabs model next to each voice in the Voices table | `pipeline/script_md.py` | In the patch |
| The docstring's v4 example without `seed` or `voice_settings`, tags, `"lang"` | `cast.py` | In the patch |
| `CAST_V4`, `FINAL_V4`, `TAGS` (the NARRATOR (TRAILER) row only once check 18 confirms it), the `NM_VOICES` override (an unknown value stops); `selftest.py` checks the three casts and the stop | `cast.py` | Done; `TAGS` is data until the house-style lint reads it. The remake reads its voices from `CAST_V4` |
| Each Voice Design prompt, preview text and design date as a comment beside its `voice_id`; for a Library voice, its ID, sharing terms and the soundalike check | `cast.py` | To do, at design time |
| Cast table: a "Final voice" column beside "Scratch voice", with each prompt (or a pointer to its `cast.py` comment) | `SERIES.md` | Started: a "Final voices" note under the table; the column once the voices exist |
| End card: "Footage, reenactments and voices made with AI." on every episode with a reenactment, whatever the cast (the remake first); "Reenactments and voices made with AI." on one without, when its soundtrack holds an ElevenLabs voice or a locked v4 take, read from `timeline.json` (the re-voiced Confessional first) | `pipeline/render.py` (`render_end()`); the remake's end `note` says it | Done |
| Description lines ("Written by [NAME]." plus the end card's first line, then "The flamingo is real.") and labels | `channel/CHANNEL.md` (`channel/CHANNEL_LEGACY.md` is kept frozen as a record) | Done |
| The disclaimer quoted as the label-proof joke | `.agents/skills/ai-tiktok-series/SKILL.md`, `.agents/skills/ai-tiktok-series/references/posting-playbook.md`, `.agents/skills/ai-tiktok-series/references/new-show-checklist.md` | Done in `references/posting-playbook.md` (the widened line, as a lesson); the show-agnostic examples in `SKILL.md` and `new-show-checklist.md` stay |
| "Voices" section: scratch (Kokoro) and final (v4) voices, tags, locking takes, cost | `README.md` | Done ("Final voices: Eleven v4"); until the takes lock lands it keeps a take by copying it to `recordings/<rec>.v4.wav` |
| House rules for tags and pauses (untagged by default, candidates on button lines only), and a tagged button line in the template | `.agents/skills/nobody-moves-write-episode/SKILL.md`, `references/episode-template.py` | Done |
| Designing voices (check 0 first, no Library narrator, the soundalike check), the settings matrix, the voice test (one re-voiced video, visuals unchanged) and its win rule, 3 takes a line then the human fallback, takes, `--revoice`, cost check before a build | `.agents/skills/nobody-moves-produce-episode/SKILL.md` | Done (the takes lock itself is still to build) |
| Re-measure every re-voiced episode with mixcheck; dialogue clips may now contain non-verbal sounds; quiet-tagged lines and the CHIME's level | `.agents/skills/nobody-moves-sound-design/SKILL.md` | Done |
