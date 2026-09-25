# Concept scorecard: finding the channel idea

This is how NOBODY MOVES was chosen: a 5-phase process run by 15 agents over about 45 minutes. Run it again for a new show, with fresh research, because short-form trends turn over in weeks. The findings at the end are dated September 2026.

## Contents
1. The method
2. Hard gates
3. The three lenses
4. What to deliver
5. Worked example: the 15 candidates
6. Research findings (September 2026)

## 1. The method

If your host can run parallel subagents, give each role below to its own agent and collect structured output. Otherwise run the phases yourself, in order, and keep the roles separate. A judge that also wrote the concepts scores its own work too kindly.

1. **Research (2 briefs, web search).**
   - *Landscape:* which AI comedy formats and accounts are working right now, with rough follower and view counts; which formats are saturated or burned out; the retention mechanics that work (hook style, length, recurring cast, cliffhangers, comment bait); and the anti-"AI slop" backlash.
   - *Operations:* what the tools can really do for one person (keeping characters consistent, lip-sync, clip length, cost per finished 30–60 s video); TikTok's AI-content (AIGC) labels and rules on real people; Creator Rewards eligibility; IP and likeness risk.
   - Each brief returns a summary, findings (name, detail, evidence, saturation low/medium/high), an **avoid** list and sources.
   - Say when evidence is thin. In this environment web fetch was blocked and TikTok and YouTube were unreachable, so the research came from search-result summaries. Tell the user that.
2. **Ideate (5 writers × 3 concepts = 15).** Each writer takes one angle and gets the research brief:
   - `serial`: a recurring-character sitcom or soap, with continuity, running gags and cliffhangers.
   - `mockdoc`: a mockumentary, nature doc or news parody, with deadpan, prestige-style narration applied to mundane or absurd subjects.
   - `hijack`: native TikTok formats (GRWM, storytime, day-in-my-life, unboxing, POV, podcast clips) performed by absurd, completely sincere AI subjects.
   - `interactive`: comments, polls and replies shape what happens next.
   - `relatable`: universal everyday situations escalated to absurd, cinematic extremes.

   Every concept has: `name` (with a handle idea), `logline`, `format` (a typical video, beat by beat), `series_engine` (why it can produce 100+ episodes), `why_funny` (the mechanism, not "it's absurd"), `sample_episodes` (at least 3), `ai_pipeline` (which tool does what, with time and cost per video) and `risks`.
3. **Judge (3 lens judges).** Each judge scores every concept 1–10 through one lens only (section 3), and must use the full range instead of clustering at 6–8. Weighted score = 0.4 × comedy + 0.3 × feasibility + 0.3 × risk.
4. **Prior art (top 4).** An adversarial agent tries to prove each finalist is *not* original. It searches several phrasings, the key characters, and "AI" plus the genre. It returns `already_exists`, `closest_existing` (accounts, platform, rough size), `originality` 1–10 and a concrete `differentiating_twist`.
5. **Synthesize.** Write the pitch (section 4). The synthesis may override the ranking if prior art shows a finalist already exists.

## 2. Hard gates

A concept that fails any of these is out, whatever it scores. Each one is a way a channel gets removed, demonetized or mass-reported.

- **No real people:** no celebrities, politicians, influencers or private individuals, no likenesses and no cloned or soundalike voices.
- **No copyrighted or trademarked characters,** and no brand-lookalike characters.
- **Not aimed at kids.** The kids category is the most slop-saturated and the most scrutinized.
- **Label-proof.** The joke still works when viewers know it is AI; it leans into being AI instead of trying to fool anyone. Nothing that only works as a hoax (fake Ring-cam animals, fake street interviews).
- **Not mean-spirited:** no stereotypes, and no rage-bait escalation.
- **Human-written.** A person writes it (and ideally voices it). Fully automated faceless pipelines get flagged as unoriginal.

## 3. The three lenses

Give each judge its lens verbatim.

| Lens | Weight | The judge's brief |
|---|---|---|
| Comedy and retention | 0.4 | Is it actually funny, not just random? Does the first 1–2 s hook a scroller? Rewatchability, shareability ("send this to your group chat"), comment bait, and whether the joke survives episode 30. Be a harsh comedy editor; most AI comedy is not funny. |
| Production feasibility | 0.3 | Can one person make 3–5 videos a week, cheaply? Does it depend on things AI still does badly: long lip-synced dialogue, precise character consistency, physical comedy timing, readable on-screen text? Penalize concepts whose humor collapses if the generation looks janky; reward concepts where AI jank is part of the charm. |
| Originality, platform and business risk | 0.3 | How saturated is the niche? Would AIGC labels, "unoriginal content" rules or the slop backlash hurt it? Any likeness, IP or defamation risk? Can it earn money (Creator Rewards, brand deals, merch)? A higher score means safer and more original. |

What scored well, and why, for use as tie-breakers:
- **A visual rule that matches what AI does well.** Stills and camera moves, no lip-sync, no humans on screen. "Stillness is what AI renders best."
- **A known TV format aimed at tiny stakes.** The comedy is the gap between prestige form and petty content (the *American Vandal* mechanism).
- **A fixed non-human cast, each with one comic mechanism.**
- **A repeatable engine with fair comment bait:** a question viewers can answer from frames they've already seen.
- **Captions carry the joke,** because most viewers watch muted.

## 4. What to deliver

Show the user 3–5 concepts, each with its lens scores, weighted score and one-line reason, then recommend one. Aim for 700–1100 words, skimmable, with no preamble:

1. **The pick:** the name and handle, a one-line pitch, why it works (the comic mechanism, tied to the research), and the prior-art twist.
2. **The format template:** beat by beat, with timings. NOBODY MOVES:

   | Time | Beat |
   |---|---|
   | 0–2 s | Hook: an extreme close-up and one deadpan line ("I've been standing in this exact spot for thirty-one years. I didn't see nothing.") |
   | 2–5 s | Title card over a dusk establishing shot, with a piano sting |
   | 5–45 s | 2–3 witness interviews (a still with a push-in, a lower third, interviewer questions as text), true-crime B-roll, an anonymous source with a distorted voice |
   | 45–60 s | One new clue, then a cliffhanger |
   | 60–70 s | Doorbell cam: "Comment the object + timestamp" |

3. **Six episode ideas.**
4. **How to make it:** the pipeline, time and cost. With this repo's pipeline, voices and score cost nothing (local TTS, synthesized audio). With third-party tools, the pitch estimated 2–3 hours and $5–15 per episode plus $50–90 a month.
5. **Growth and money:** see `posting-playbook.md`.
6. **Two runners-up,** each with why it lost.
7. **What to avoid.**

Close by telling the user to search TikTok in the app for the premise's key phrases ("gnome true crime", "lawn ornament documentary") and to claim the handle. The prior-art check can't see inside TikTok from here, so it is partial.

## 5. Worked example: the 15 candidates

The winner's lens scores were comedy 7, feasibility 9 and risk 8.5, so 0.4 × 7 + 0.3 × 9 + 0.3 × 8.5 = **8.05**.

| # | Concept | Score | Note |
|---|---|---|---|
| 1 | **NOBODY MOVES**: a prestige true-crime docuseries on one cul-de-sac where every witness is a lawn ornament. "Somebody moved the flamingo." | 8.05 | Picked. Prior-art originality 6; closest were Fruit Love Island, AI "interviews with inanimate objects", gnome vlogs, and an AI true-crime parody whose views dropped once labeled. |
| 2 | SOCIAL CRASH TEST: a government lab crash-tests awkward social moments in slow motion | 7.25 | An existing account (~410K followers) already owns the lab-dummy look; awkward-moment comedy is saturated; flying limbs risk violence filters. |
| 3 | Midnight Zone: deep-sea creatures run an influencer house. "The video is AI. The biology is real." | 7.1 | Lip-sync on fish mouths is hard; AI animal accounts are saturated; skews young; overlaps a famous deadpan biology series. |
| 4 | It's Always Been Like That, Doug: a 90s claymation sitcom where only Dad notices the continuity errors | 6.85 | |
| 5 | THE LATE HUMANS: crab news from the year 52,026, explaining our junk | 6.85 | |
| 6 | FCN: Family Chat Network: felt-puppet cable news covering a family group chat | 6.85 | |
| 7 | Guess the Humans!: an anglerfish-hosted game show | 6.5 | |
| 8 | LATENT PLANET: a nature doc about AI-video glitch "wildlife" | 6.3 | |
| 9 | Department of Minor Inconveniences: a felt-puppet civil service | 6.3 | |
| 10 | The Junk Drawer: obsolete gadgets plotting a comeback | 6.2 | |
| 11 | As the Board Turns: a soap opera about park chess pieces | 5.7 | |
| 12 | Lair Rescue with Brenda: a gorgon business consultant | 5.7 | |
| 13 | Top Comment Is King: a claymation kingdom ruled by the top comment | 5.7 | |
| 14 | BOSS FIGHTS OF ADULTHOOD | 4.95 | |
| 15 | Unholy Grind: a dark-lord hustle podcast | 4.9 | |

**Why the winner won, in the judges' words:**
- "The joke is built into the premise." "Every alibi is 'I was standing right here.'" "Frozen ceramic faces are deadpan without any acting."
- "AI is best at things that don't move." "No rubbery faces, no lip-sync, no humans on screen." AI flaws become canon: the goose's outfit changes between cuts.
- **The prior-art twist:** make "nobody moves" a strict rule. Each witness is a still with voiceover and a slow push-in, and every episode ends on a doorbell-cam still where one object has shifted. Viewers comment the object and the timestamp, and the finale's answer can be proven from earlier frames. That makes it "a game people rewatch frame by frame".
- **Series engine:** it borrows Fruit Love Island's mechanics (a known format, a fixed cast, cliffhangers, voting, new arrivals) and drops what failed. Seasons are new petty mysteries on the same street; seasonal arrivals come free (the October skeleton, holiday inflatables); unseen humans become mythology ("The Mower"). "The vote only picks who gets interrogated next, never the solution, so the writer keeps control of the ending."
- **The comedy judge's caveat:** "60-90s static talking heads bleed watch time, and the humor is chuckle-level more than share-level." The pilot's answer was a 2-second hook, a new shot about every 6 seconds (question cards, evidence flashes, the doorbell cam), and captions written as punchlines.

## 6. Research findings (September 2026)

**Saturated or risky; steer away:**
- Fruit, vegetable or candy "Love Island" microdramas.
- AI cat and animal soap operas.
- Italian brainrot characters.
- AI baby podcasts.
- Bigfoot, Yeti or Stormtrooper selfie vlogs.
- Photoreal AI street interviews.
- Fake doorbell or Ring-cam animal hoaxes, and anything else built on fooling viewers.
- "POV: you wake up in 1351" history.
- Channels built only on one-click effect trends.
- Real-person likeness and voice clones; copyrighted characters.
- Kid-targeted content; rage-bait escalation.
- Fully automated faceless pipelines.
- Arguing with anti-AI commenters.

**The case study: Fruit Love Island.** About 3.3M followers and 300M views in about 10 days in March 2026, then a collapse within about two weeks: 12 of 22 episodes were removed after mass reporting, viewers complained about the lip-sync, and the creator quit. The lesson: "What made it work was the format, not the fruit." It had a known TV structure, a fixed cast, cliffhangers, several posts a day and viewer voting. "The audience followed the posting pace, not the creator."

**The open lane: the "Neural Viz model".** A fixed cast of stylized non-human characters in a TV-parody format (mockumentary, sitcom, news or reality show), written and voiced by a person, clearly labeled, and posted as numbered episodes.

**Policy and money (verify again; several points came from single or third-party sources):**
- TikTok requires AI labels on realistic content and detects AI automatically. Viewers now have a slider to see less AI.
- TikTok bans AI likenesses of minors and private people, and of public figures in endorsements or misleading content.
- Creator Rewards needs original videos of 60 s or more (plus 10k followers and 100k views in 30 days). Eligibility for fully AI videos is uncertain, so treat it as a bonus, not the business.
- Purely AI-generated characters are probably not copyrightable. Keep evidence of human authorship: scripts, voice takes, edit files.
- Commercial rights for AI voice and music tools usually need a paid plan.
