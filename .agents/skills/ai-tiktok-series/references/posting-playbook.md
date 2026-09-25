# Delivery specs and posting playbook

## Contents
- Delivery specs
- Reels and Shorts
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

## Reels and Shorts

The same upload copy works as an Instagram Reel and a YouTube Short: the same frame, codec and loudness. No second render is needed. What differs:

| | TikTok | Instagram Reels | YouTube Shorts |
|---|---|---|---|
| Length | 60–90 s for main episodes | up to 3 minutes | up to 3 minutes |
| UI over the video (approximate, 1080×1920) | top 130 px; buttons x 940+ from y 880; description y 1500+ | top 200 px; buttons x 950+ from y 1100; description y 1500+ | top 160 px; buttons x 960+ from y 1000; description y 1540+ |
| AI label | "AI-generated content" | "AI info" (Meta asks for it on photorealistic AI video and realistic voices) | "Altered or synthetic content" in YouTube Studio |
| Cover | pick a frame | pick a frame; the profile grid crops it to 3:4, cutting 240 px from the top and the bottom | pick a frame (mobile upload) |
| Money | Creator Rewards (60 s or more) | Reels bonuses are invitation-only and change often | Shorts revenue sharing through the YouTube Partner Program |

- **Check the layout for all three.** `review.py` runs `pipeline/safezones.py`, which flags any text under each app's buttons, top bar or description and draws `build/review/zones.png`. The zone numbers above are estimates that the apps change. Check the first upload on a phone and update `ZONES` in `safezones.py` if an app has moved.
- **Upload the clean file,** never a video saved from TikTok. The TikTok watermark looks like a repost, and Instagram has said it shows those less.
- **Keep the Reels description to one line** and the Shorts title short. Longer text expands over the bottom of the video, where the name cards are.
- **Don't boost an episode as a Reels ad as it is.** Meta's ad guide keeps text out of the bottom 35% (from y 1248), where a sponsored Reel's button sits and where the name cards and calls to action are. `safezones.py` lists those shots as "Reels ads" info. Cut a separate ad instead.
- **YouTube re-compresses everything,** so the master (`build/<ep>.mp4`) looks a little sharper there than the 29 MB upload copy. Use it when you have it.
- **Pin and link the start on every platform:** pin Episode 1 on Instagram, and put the episodes in a YouTube playlist, linked from each Short.

## Labeling and disclosure

- **Turn on the AI label** on every post: TikTok's AI-generated content label, Instagram's "AI info", YouTube's "altered or synthetic content". The format is built to work with the label on.
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
