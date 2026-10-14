# Test plan: the Episode 1 remake, and the voice test beside it

## Two tests, and what each one can tell you

The remake ships with Eleven v4 voices (D9), so its test against the published Episode 1 changes picture and voice together. A second test changes the voice alone.

| Test | A: the published video | B: the new video | What differs | A difference is attributable to |
|---|---|---|---|---|
| **Voice test** | The Garrison Confessional (`ep05c_garrison_doorbell`), Kokoro voices | The same Confessional re-voiced on Eleven v4: the designed GARRISON and NARRATOR voices, with its two tag candidates kept only if they won the blind pick | The voices, the timing that follows from their takes, and the end card's first disclosure line. Stills, edit, captions and music are unchanged | **Garrison's v4 voice** (7 of its 8 lines; the narrator has one). LORRAINE, the CHIME, the trailer register and 4 of the remake's 5 tags never appear in it, so this test can't speak for them |
| **Package test** | Episode 1 (`Pa5h60evtv0`), stills and Kokoro | The remake (`ep01r_three_feet_reenacted`): 3D reenactments, the remake's structure (cold open, pace, brightness, early question) and v4 voices | Everything | **The whole package.** No single element can be credited from this test alone |

**Reading the two together.** Each result is win, loss, flat or inconclusive against its own rules (below):

| Voice test | Package test | What it means |
|---|---|---|
| Win | Win | Garrison's v4 voice helps on its own. The rest of the remake's win is the best estimate of what the format, the structure and the publicly untested voices (narrator, Lorraine, chime, trailer) add together; nothing isolates them |
| Flat | Win | Garrison's voice doesn't explain the win. The narrator, Lorraine and chime voices and the tags stay confounded with the format until the replication |
| Loss | Win | The format won despite the voice: strong evidence for the format. New episodes stay on Kokoro |
| Win | Flat or loss | Garrison's voice helps; the reenactment format and the remake's structure don't, or cost more than the voices add |
| Flat | Flat or loss | Neither is holding the channel back. Look at packaging and posting cadence |
| Loss | Flat or loss | Uninterpretable for the format: B carried a voice already shown to lose. Decide the format by the replication Confessional voiced on Kokoro against A2 (criterion 5), not by "Stop" |
| Inconclusive | Any | Read the package test as the whole package only |

**Not attributable in public at all:**
- **Tags against no tags.** Each tag is decided inside the team by a blind pick against an untagged take of the same line ([`docs/AUDIO_ELEVENLABS_V4.md`](../../docs/AUDIO_ELEVENLABS_V4.md), "Rollout and A/B").
- **Reenactments against the rest of the restructure.** Both are in B. The replication Confessional (criterion 5), judged against the Garrison Confessional on the same voices, is the step that isolates the reenactment.
- **Human against v4 takes.** Human takes appear only as the fallback for a line no v4 take landed in 3 tries. Record how many there are (the plan is none).

## Order (D9)

1. **The voice test first.** It needs the four designed voices (the remake needs them anyway), filled into `cast.py`'s `CAST_V4`, but no clips; `NM_VOICES` and the end card's "voices" wording (`render.py`) are already built. Post it on the first Thursday after the voices are locked, at about 15:15 UTC, the slot both top Confessionals used: 2026-10-15 at the earliest.
2. **The package test at least 7 days later,** once the remake passes its gate, in A's slot: a Monday at about 20:05 UTC. 2026-10-26 at the earliest. Its 48 h read then comes after the voice test's 7-day read, so the two never overlap.
3. **The replication Confessional after B's 7-day read** (criterion 5), voiced to match its baseline.
4. **Each one posts alone:** at least 48 h after the previous upload, and nothing else goes up until its 7-day read. Read at 48 h, decide at 7 days, re-check at 28 days.

The voice test doesn't change what the remake ships with: it ships v4 either way (D9). It decides Garrison's place in the series default voices (`FINAL_V4`; the other voices also need the internal check), how to read the package test, and how the replication is voiced.

---

## Package test: the remake against the published Episode 1

| | A: published Episode 1 | B: remake |
|---|---|---|
| Video | "Episode 1: Three Feet \| NOBODY MOVES #Shorts" (`Pa5h60evtv0`) | "Three Feet, Reenacted" (`ep01r_three_feet_reenacted`) |
| Posted | Mon 2026-09-28, 20:05 UTC, in a batch of four episodes within about 95 minutes | Alone, at least 7 days after the voice test (see "Order") |
| Length | 80 s | 46.9 s on the Kokoro scratch voices; under 50 s on the v4 takes |
| Voices | Kokoro | Eleven v4, designed voices; five tagged lines |
| Shape | Opens on a gnome close-up, then a 3.2 s title card at 0:05. The comment ask comes at 1:13. 26 s nearly black | Opens on the doorbell event at 0:01, with no title card. A binary comment question at 0:08.4 (Kokoro scratch timeline), two reenactments labelled REENACTMENT · AI, Mr. Basin as a silent cutaway, the real footage stamped NOT A REENACTMENT, and a captioned closing button. The frame-418 bonus is kept |
| Views so far | 31 | — |

This tests the whole package against the original: the reenactment format, the remake goals (cold open, pace, brightness, early question) and the v4 voices. It decides whether B wins and is pinned, and is the first half of the go/no-go for converting the series to reenactments (the replication is the second). On its own it cannot say which element made the difference; read it next to the voice test.

### Before posting B (the gate)

- **Real clips, not fallbacks.** `render.py` prints no `REENACTMENT FALLBACK`. A remake whose reenactments don't move is testing the wrong thing.
- **Checks pass:**
  - `review.py` shows no FAIL, and `reenact.png` passes the checklists in `REENACTMENT_PROMPTS.md` (including the cap and beam clear of the red tag);
  - `mixcheck.py` passes, including the "reenactment cut" check;
  - `safezones.py` shows the red tag (with the long Director's Cut stamp) and the call to action clear of every app's chrome.
- **The v4 voices, locked.** Every line is a chosen v4 take, kept in `takes/` (or, until the takes lock lands, copied to `recordings/<rec>.v4.wav`: the `.v4` keeps it an AI voice on the end card and in `SCRIPT.md`), with the five tagged lines picked blind against an untagged take. `heist_1` and `action_1` were locked before their clips were generated, and each clip's hold time was set from its take (`NOTES.md`, length rule). A line that no v4 take landed in 3 tries is recorded by a human (the ★ list in `SCRIPT.md`). Record the number of human lines.
- **The timeline on the locked takes** (D1, D7). Copy the Kokoro build's `build/timeline.json` aside before locking any take (a recording wins over every cast, so a take copied without `.v4`, or a human take, makes `NM_VOICES=kokoro` no longer Kokoro for that line; `.v4` takes are skipped under it). Build the audio on the locked takes and run `tools/fit_takes.py --ref <the Kokoro build's timeline.json>`: under 50 s, about 165 words/min while speaking (every take within its Kokoro length +5%; never under 150) and 110–120 overall. Over 49.5 s, apply `NOTES.md`'s trim list in its order; never the cut-back holds, the call-to-action hold or the 2.6 s end card. A reenactment line that came back longer has raised its shot's `dur` (at most 6.0 s), and its clip was generated against the locked take.
- **Read points from the shipped build.** Copy the ask, the first move, both cut-backs, Mr. Basin and the call to action from the shipped build's `SCRIPT.md` or `timeline.json` into metrics #2 and #4 and the results sheet before posting. The times written below are from the Kokoro scratch build.
- **Muted phone check.** Watch it once on a phone with the sound off. Every joke has to read from the picture and captions, including Mr. Basin's card ("Birdbath · Declined to comment" over the yellow "Facing: up.", fully on from the cut to the hard cut) and the closing button ("They made me look short.", captioned on its own still because end cards draw no captions).
- **Disclosure check.** Every reenactment frame carries "REENACTMENT · AI" (D4). On the end card, "Footage, reenactments and voices made with AI. The flamingo is real." is fully legible for at least 1.8 s (D3: it fades in with the title on any episode with a reenactment, and `validate()` fails the build otherwise).

### Keep identical

| Item | A | B |
|---|---|---|
| Platform | YouTube Shorts | YouTube Shorts only during the test. TikTok and Reels split the audience, and their numbers can't be compared with A's. Cross-post after the 7-day read. |
| Title pattern | `Episode 1: Three Feet \| NOBODY MOVES #Shorts` | `Episode 1: Three Feet, Reenacted \| NOBODY MOVES #Shorts` |
| Description | Logline, then "Something else in frame 418 moved. Comment the object and timestamp before Episode 2.", then the disclosure and hashtags | A's logline and hashtags, with three differences to record: the bonus line reads "Something else in frame 418 moved. Comment what changed before Episode 2." (asking for "the object" invites a bare "goose", which is also a poll vote); the disclosure line reads "Written by [NAME]. Footage, reenactments and voices made with AI. The flamingo is real."; and one added line: "Reenactments are theories. Nothing in this yard moves while anyone is watching." |
| Tags | `NOBODY MOVES, Three Feet, true crime parody, lawn ornament mystery, flamingo, mockumentary` | Same, plus `reenactment` |
| AI disclosure | "Altered or synthetic content" on. The end card's "Reenactments dramatized with AI. The flamingo is real." is fully legible for about 1.8 s of a 3.6 s card | The same toggle, on. **Not identical on screen:** B contains real AI video and v4 voices, every reenactment frame says "REENACTMENT · AI", and its end card's disclosure ("Footage, reenactments and voices made with AI.") fades in with the title, so it is fully legible for 1.95 s of a 2.6 s card. Record this as a difference; it can only make B more cautious, not less. |
| Cover | The channel's cover template | Same template. The feed shows the video, but the channel grid and search show the cover. |
| Playlist | Season 1 | Season 1, right after A |
| Pinned comment | A's | Same style: point at the bonus without naming it ("Something else changed at 0:01. Don't spoil it for the next person.") |
| Promotion | None | None: no community post, no shared links and no cross-posts until the 7-day read |
| A during the test | — | Don't edit, re-pin, unlist or re-upload A. **The current pin stays through the 7-day test (D6);** "Episode 1 is pinned" keeps pointing at A until then. After B's 7-day read, B is pinned if it won criteria 1–4; otherwise A keeps the pin. |

### When to post

- **Post B alone,** in the order above. A shared its first hours in the feed with three other episodes. B won't, and that favours B, so the per-impression rates below matter more than views.
- **Use A's slot:** a Monday at about 20:05 UTC, at least 7 days after the voice test went up. If you'd rather post B in a Thursday 15:15 UTC slot, record it as another difference from A.

### Metrics

Compare B's first 7 days with A's first 7 days (2026-09-28 to 2026-10-05). Read them in YouTube Studio: the video, then Analytics, then Advanced mode with a custom date range. Write every number with its denominator.

| # | Metric | Where in Studio | Why it matters here |
|---|---|---|---|
| 1 | **Viewed vs swiped away** (% of Shorts-feed impressions that stayed) | Engagement, or Audience retention for Shorts | Measures the hook. Its denominator is feed impressions, not views, so it is the most usable number at this scale. |
| 2 | **Retention at fixed seconds**: 0:03, 0:10, 0:20, 0:30 and 0:40. For A also its title card (0:05) and its ask (1:13) | Audience retention graph | Read B's curve at the shipped build's timecodes (gate): the first move, the two hard cuts back, and Mr. Basin's silent cutaway. On the Kokoro scratch build they are 0:13.0, 0:14.8 and 0:24.1, and 0:17.8. A drop there means the cut loses people; a bump means the joke lands. |
| 3 | **Average view duration** and **average percentage viewed** | Overview | B is about 40% shorter (46.9 s on Kokoro, under 50 s on v4), so its percentage viewed is flattered. Use #2 to compare like with like. A percentage above 100% means people looped it, which is what "Rewatch 0:01" asks for. |
| 4 | **% who reached the comment ask** | The retention curve at A's 1:13 and at B's ask in the shipped build (0:08.4 on the Kokoro scratch build) | The remake's main structural bet. |
| 5 | **Engaged views** and **views** | Overview | Since March 2025, Shorts "views" count every start and replay; engaged views is the old count. Report both, and don't mix them. |
| 6 | **Comments**: total, per 100 engaged views, poll votes (gnome / goose), and frame-418 finds | Comments | The baseline is 0 comments across all 20 Shorts. The goose is both a suspect and the hidden change, so count a **find** only when the comment says how she changed (turned, facing, rotated, backwards) or points to the porch, 0:01 or 418. A bare "goose" is a poll vote. |
| 7 | **Shares** per 100 engaged views | Engagement | |
| 8 | **Subscribers gained** from the video | Audience | |
| 9 | Traffic sources (Shorts feed, channel page, playlist, search) | Reach | If most of A's 31 views came from the channel page rather than the feed, only feed-based rates (#1) are comparable. |

Also record the cost of B: generation attempts, money and hours per reenactment clip, v4 characters billed and takes per line, each take's words/min, and the number of human fallback lines. A win that costs five times more to make has to be a big win.

### What the results decide

Decide in two steps, against these thresholds, fixed before posting.

**B wins the package test** when criteria 1–4 hold at B's 7-day read. B is then pinned as Episode 1 (D6). B keeps Episode 1's plants (Exhibit A, Exhibit B with "where she stood for thirty years" and the drag tracks, the chime's "…very windy", "I was facing the other way"), so Season 1's later episodes still make sense after it.
1. **Hook:** B's viewed-vs-swiped-away rate beats A's by more than the difference margin below (for example, more than 20 points at 50 impressions each). B must have at least 50 feed impressions.
2. **Retention:** B keeps at least twice A's share of viewers at 0:20. B's average percentage viewed is at least 70%.
3. **Reach:** B's 7-day engaged views are at least twice A's 7-day engaged views.
4. **Action:** at least three comments or two shares on B, and at least one comment that answers "Gnome, or goose?". The channel has never had a comment.

**Convert the series** when B won and criterion 5 also holds at the replication's own 7-day read. Reenactments then become standard in new main episodes, and the Episode 2 remake comes next (on the remake's v4 voices; see the voice test's follow-ups).

5. **Replication:** one more reenactment video also beats its own baseline, on the same voices as that baseline. The cheapest candidate is the proposed Confessional "Garrison watches his 3D double" ("That isn't me. … They cleaned my hat."), with one reenactment of 5 s or less.
   - **Voiced to match its baseline.** If the voice test won, voice it on v4 and require its viewed-vs-swiped-away rate to be at least B2's (the re-voiced Confessional: v4, no reenactment). Otherwise, voice it on Kokoro and require at least A2's (the published one). Either way it differs from its baseline only in the reenactment.
   - It also needs more views than the Confessional median (28).
   - It posts after B's 7-day read. It ends on "Episode 1 is pinned." only if B was pinned; if A kept the pin, it ends on "Three Feet, Reenacted is in the playlist." ([`SERIES.md`](../../SERIES.md), "Confessionals").
   - Without a replication, one good post may be luck.

**Iterate, don't convert,** when B clears 1 and 2 but not 3 and 4. A keeps the pin. The format holds viewers but doesn't make them act. Keep it, change the ask (for example a pinned "Gnome or goose? Vote below" comment, or the question on screen sooner), and test again on the Episode 2 remake.

**Stop** when B fails to beat A on 1 or 2 by more than the margin, after at least 50 feed impressions. A keeps the pin. If the voice test was flat (not a loss), neither the reenactments nor the voices are what's holding the channel back: look at packaging (titles, the first frame) and posting cadence instead, and keep the series in stills. If the voice test won, keep Garrison's voice and drop the format. If the voice test lost, don't stop on this result: B carried a voice already shown to lose, so the replication Confessional, voiced on Kokoro against A2, decides the format.

**Inconclusive** when B gets fewer than about 50 feed impressions in 7 days. A keeps the pin. The feed never tested it. Post the replication Confessional and read the two together before deciding anything.

In every outcome A stays up, because Season 1's later episodes refer back to it. B is pinned only if it won criteria 1–4 at its 7-day read (D6); in every other outcome A keeps the pin.

**Runtime (D7).** Main episodes stay under 50 s, for retention. TikTok's 60 s Creator Rewards minimum, which main episodes were first written for, is revisited near eligibility, not in this test.

---

## Voice test: the re-voiced Garrison Confessional

| | A2: published Garrison Confessional | B2: re-voiced |
|---|---|---|
| Video | `ep05c_garrison_doorbell`, 21.5 s, posted on a Thursday at about 15:15 UTC | The same episode built with `NM_VOICES=v4` |
| Voices | Kokoro: am_fenrir pitched ×0.86, bm_george | The designed GARRISON and NARRATOR voices on `eleven_v4` (the same voice IDs as the remake). Its candidates "Nosy." `[with contempt]` and "...I was facing the other way." `[flatly]` stay only if they win the blind pick |
| Picture | Stills, captions, music, edit | Identical. Shot lengths follow the new takes; record the new runtime |
| End card | "Reenactments dramatized with AI." / "The flamingo is real." | "Reenactments and voices made with AI." / "The flamingo is real." (no reenactment, so not the remake's "Footage, …" line; a difference to record) |
| Views so far | 120 (the channel's best Short) | — |

**What it can credit:** Garrison's v4 voice. Seven of the eight lines are his; the narrator has one 25-character line, and LORRAINE, the CHIME, the trailer register and four of the remake's five tags never appear.

**Before posting B2:** every take locked and picked blind; no v4 voice more than 0.5 lower than Kokoro on "in character" in the internal check ([`docs/AUDIO_ELEVENLABS_V4.md`](../../docs/AUDIO_ELEVENLABS_V4.md), "Blind picks"); `mixcheck.py` passes, including dialogue over bed on every line; a muted phone check (nothing changed on screen, so it should pass as A2 did); the end card reads "Reenactments and voices made with AI." (`render.py --preview <end start + 1.9>`): every locked take is in `recordings/<rec>.v4.wav`, since a take copied without the `.v4` counts as a human take and drops "voices".

**Keep identical:** YouTube Shorts only until the 7-day read; A2's title and tags word for word; A2's description word for word with the disclosure line as "Written by [NAME]. Reenactments and voices made with AI. The flamingo is real."; the same cover; the Confessionals playlist, right after A2; no promotion. Don't edit, re-pin, unlist or re-upload A2.

**Metrics:** the same table as the package test (#1 to #9), B2's first 7 days against A2's first 7 days, plus **returning viewers %** (Studio > Audience) for both. Read retention at 0:03, 0:10 and 0:20, and around "...I was facing the other way." (A2's climax, after its `P(0.7)`), where the voice does the most work. Before reading B2, confirm Studio shows no limited-distribution or reused-content notice on it: B2 is a near-duplicate of A2.

**Two baselines.** A2 is the channel's best Short (120 views against a Confessional median of 28), so its rate is probably a high draw. B2 is a near-duplicate shown to an audience that partly saw A2, which lowers its rate whatever the voice does. Both push toward "loss", so the voice test also reads the **median viewed-vs-swiped-away rate of the other five Confessionals** (their first 7 days, read the same way).

**Decide at 7 days:**
- **Voice wins** when B2's viewed-vs-swiped-away rate beats A2's by more than the difference margin, with at least 50 feed impressions, and its average percentage viewed is not more than 10 points below A2's. GARRISON goes into `FINAL_V4`. The NARRATOR, LORRAINE and the CHIME go in only after passing the internal per-character check (not more than 0.5 below Kokoro on "in character", and "clear" on a phone speaker), and the record says they weren't tested in public.
- **Voice loses** when B2's rate is below both A2's and the five-Confessional median by more than the margin, after at least 50 feed impressions. New episodes stay on Kokoro, and the voices are redesigned before another try. The remake keeps the v4 voices it shipped with.
- **Flat** when B2 falls between those (within the margin of A2, or below A2 but not below the median by more than the margin): keep Kokoro for new episodes, and read the package test as the whole package only.
- **Inconclusive** under 50 feed impressions: the same as flat.
- **The package's follow-ups, in every outcome.** "New episodes" above means episodes outside the reenactment test. The Episode 2 remake belongs to the reenactment package and uses the remake's v4 voices whatever this test says; if the voices are redesigned, re-voice the remake with them before the Episode 2 remake. The replication Confessional is voiced to match its baseline (criterion 5).

Count a comment about the voice ("he sounds different", "new voice?") as a signal either way, and record it.

---

## Reading results at this scale

- **A single view count proves nothing.** The six Confessionals used the same template and got between 2 and 120 views. Main episodes range from 2 to 82. One post is one draw from a very noisy distribution. The voice test's A2 is the channel's best Short, so B2 has to beat a high bar; its rates matter more than its views, and a loss needs B2 under both baselines.
- **Use rates, with margins.** For viewed-vs-swiped-away, the rough 95% margin on one video's rate, and on the difference between two videos with similar impressions:

  | Feed impressions per video | One rate | Difference between A and B |
  |---|---|---|
  | 25 | ±20 points | ±28 points |
  | 50 | ±14 | ±20 |
  | 100 | ±10 | ±14 |
  | 200 | ±7 | ±10 |

  A difference smaller than the right-hand column is noise.
- **Fix the thresholds before posting.** They are above. Don't move them after seeing the results, and don't stop early because the 48 h read looks good or bad.
- **Separate distribution from format.** If B wins on views but not on rates #1–#4, the feed showed it more, but viewers didn't like it more.
- **Add a second baseline for the package test:** one solo main episode, S2E2 (posted alone on Sat 2026-10-03, 19:05 UTC, 10 views). Read its same metrics.
- **Read every comment.**
  - "Why do they move now?" or "So the gnome did it?" means the REENACTMENT · AI label isn't doing its job.
  - "The goose turned around", "she's facing the other way at 0:01", "look at the porch in 418": the bonus works. A bare "goose" or "it's the goose" is a vote, not a find.
  - Votes for gnome or for goose mean the easy question works.

## Results sheets (fill in at 48 h and 7 days)

**Package test** (B's read points come from the shipped build's `SCRIPT.md`; the Kokoro scratch values are in brackets)

| Metric | A, first 7 days | B, 48 h | B, 7 days | Margin | Pass? |
|---|---|---|---|---|---|
| Feed impressions | | | | — | B ≥ 50 |
| Viewed vs swiped away | | | | ± | B − A > margin |
| Retention at 0:03 / 0:10 / 0:20 / 0:30 / 0:40 | | | | — | B at 0:20 ≥ 2× A |
| B at its first move / cut-backs / Mr. Basin (Kokoro: 0:13.0 / 0:14.8, 0:24.1 / 0:17.8) | — | | | — | |
| Average view duration (s) | | | | — | |
| Average percentage viewed | | | | — | B ≥ 70% |
| % reaching the comment ask (A 1:13; B at the shipped ask, Kokoro 0:08.4) | | | | — | |
| Engaged views / views | | | | — | B ≥ 2× A (engaged) |
| Comments (gnome votes / goose votes / frame-418 finds, counted as in #6) | | | | — | ≥ 3, or shares ≥ 2 |
| Shares | | | | — | |
| Subscribers gained | | | | — | |
| Cost of B (clip attempts, money, hours; v4 characters, takes per line, words/min per take, human lines) | — | | | — | |
| Pinned after the 7-day read (B if criteria 1–4 held, else A) | — | — | | — | |

**Voice test**

| Metric | A2, first 7 days | Other five Confessionals (median) | B2, 48 h | B2, 7 days | Margin | Pass? |
|---|---|---|---|---|---|---|
| Feed impressions | | | | | — | B2 ≥ 50 |
| Viewed vs swiped away | | | | | ± | Win: B2 − A2 > margin. Loss: B2 under both baselines by more than the margin |
| Returning viewers % | | — | | | — | |
| Limited-distribution or reused-content notice on B2 | — | — | | | — | none |
| Retention at 0:03 / 0:10 / 0:20 / the alibi | | — | | | — | |
| Average percentage viewed | | — | | | — | B2 ≥ A2 − 10 points |
| Engaged views / views | | — | | | — | |
| Comments (and any about the voice) / shares / subscribers | | — | | | — | |
| Runtime, v4 characters billed, takes per line | — | — | | | — | |
