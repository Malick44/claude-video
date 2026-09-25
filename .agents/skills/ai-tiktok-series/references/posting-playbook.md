# Delivery specs and posting playbook

## Contents
- Delivery specs
- Labeling and disclosure
- Licensing
- Launch plan
- Community
- Money

## Delivery specs

| Item | Target | Why |
|---|---|---|
| Frame | 1080×1920, 30 fps, H.264 yuv420p, `+faststart` | TikTok, Reels and Shorts native vertical |
| Audio | AAC stereo 48 kHz; 192k in the master, 128k in the upload copy | |
| Loudness | −14 LUFS integrated, true peak −1.5 dBTP; each voice line RMS-matched to −17 dB | TikTok normalizes around −14; the headroom survives its transcode |
| Runtime | Main episodes 60–90 s; spin-off shorts 15–25 s | Creator Rewards needs 60 s or more; completion drops past about 90 s |
| Upload copy | `build/<ep>_tiktok.mp4`, under 29 MB | Fits the 30 MB chat attachment limit, and TikTok re-compresses to about that bitrate anyway |
| Master | `build/<ep>.mp4`, about 9 Mbps | Too big to send in chat; keep it for re-edits |

Check both files with `$FF -i <file>`, where `$FF` is the `imageio_ffmpeg` binary.

## Labeling and disclosure

- **Turn on TikTok's AI-generated content label** on every post. The format is built to work with the label on.
- **Write the disclaimer as a joke,** on the end card. NOBODY MOVES: "Reenactments dramatized with AI. The flamingo is real."
- **Put "written and voiced by [creator]" in the bio.** Human authorship is what separates the show from slop, and it is the evidence of authorship.
- **Disclose brand deals** as both paid and synthetic. Never present AI testimonials as real.

## Licensing

- Freesound searches in `pipeline/stock.py` return only CC0 and Attribution sounds, never NonCommercial ones, because a monetized TikTok counts as commercial use.
- Paste the Attribution credits from the episode's `SCRIPT.md` into the video description.
- Record the license of files the user adds with `"credit"` in the sound source.
- Commercial rights for AI voice and music services usually need a paid plan. The default pipeline avoids the issue: Kokoro runs locally and the score is synthesized in code.
- No real people, no cloned voices, no brand-lookalike characters.
- Purely AI characters probably can't be copyrighted, so keep the scripts, voice takes and edit files. Consider trademarking the show and character names once it grows.

## Launch plan

- **Write the whole season first, solution included,** and finish 8–10 episodes before launch. The posting pace is what the audience follows; a gap kills momentum.
- **Post 3–4 numbered episodes a week,** plus 15–25 s spin-off shorts (NOBODY MOVES "Confessionals": one ornament, one grudge, ending "Episode 1 is pinned.").
- **Pin Episode 1** on the profile, so every short leads new viewers to the start.
- **Search TikTok in the app** for the premise's key phrases before launch, and claim the handle.

## Community

- **Pin a hint comment, never the answer.** NOBODY MOVES: "Frame 418. Look at the porch."
- **Keep a pinned "evidence locker"** of before/after stills, so rewatchers can check their theories.
- **Reply to the best theories with video replies.** The replies are free episodes.
- **Polls pick who gets interrogated next, never the solution,** so the writer keeps control of the ending.
- **Feature followers' own objects** in the show's world (NOBODY MOVES: their lawn ornaments as "out-of-state witnesses").
- **Between seasons:** spin-off shorts, "Cold Cases", seasonal specials.
- **Never argue with anti-AI commenters.** The Fruit Love Island creator's public meltdown helped end that show.

## Money

- **Creator Rewards:** 60 s or more, 10k followers and 100k views in 30 days. Eligibility for fully AI videos is uncertain, so treat it as a bonus.
- **Merch** built on running gags (NOBODY MOVES: "FREE DEB").
- **LIVE gifts** from 1k followers.
- **Disclosed brand deals** that fit the world (for NOBODY MOVES, home and garden).
- **A paid TikTok Series** is optional; keep it separate, because Series-linked videos are excluded from Creator Rewards.
- **Cost:** with this repo's pipeline, voices and score cost nothing and the user generates the stills. With third-party tools, the pitch estimated 2–3 hours and $5–15 per episode, plus $50–90 a month.
