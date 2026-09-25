# Lessons from building NOBODY MOVES

Concrete problems hit while making the pilot and Episodes 2–3, and what fixed them. Each one cost real time once, so don't pay for it twice.

## Contents
- Network and environment
- Images
- Video and file size
- Audio and voices
- Determinism and regressions
- Writing and runtime
- Editing safely
- Long jobs and safety checks

## Network and environment

- **Blocked hosts.** Image and stock hosts were refused by policy: Higgsfield (403 on CONNECT), the Canva CDN (generation worked, but the download hosts were unreachable, so 9 generated stills could not be fetched), HuggingFace, Wikimedia, and later Freesound, ElevenLabs and Pexels. Never route around a block. Tell the user, ship everything that doesn't depend on it, and ask them to send the files or allow the host. GitHub release downloads, `raw.githubusercontent.com` and PyPI worked; that's why `setup.sh` downloads only from them. The optional sources in `pipeline/stock.py` (Freesound, Pexels, any `{"url": ...}`) and ElevenLabs voices need hosts that were blocked here; the synthesized sounds and Kokoro voices need no network at all.
- **A GitHub API call returned 403** where a plain download didn't. `git ls-remote --tags --refs <repo>` found the release tag without the API.
- **There is no ffprobe.** Use the `imageio_ffmpeg` binary: `FF=$(.venv/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")`. Get specs from `$FF -i file`; `pipeline/mixcheck.py` measures an episode's loudness with ffmpeg's `ebur128`.
- **Kokoro needs Python 3.10–3.13.** `find_python` in `tools/common.sh` searches `python3.13` down to `python3.10`. The macOS built-in `python3` is 3.9; the fix is `brew install python@3.12`.
- **espeak-ng "phontab" error.** `Error processing file '.../phontab': No such file or directory` appears when espeak-ng's data path is longer than about 160 characters (162 failed; 73, 89 and 94 worked). `check_espeak_path` warns above 150. The fix is a shorter checkout path, so keep show slugs short.
- **You can't install things on the user's computer from a cloud session.** When the user asked for Kokoro "globally on my computer", the answer was a one-command installer (`tools/install-kokoro.sh`), plus Mac notes: use `afplay` to listen.

## Images

- **Images sent while you're mid-task are not saved to disk.** They arrive as pictures only; only images in a normal message get a file path. The pilot lost an aerial and a corkboard this way. Ask the user to send the same images again in a new message. Don't ask for different images.
- **A video upload wasn't needed.** The user said "discard the video. just use image to make your video." Build from stills.
- **Two separately generated images never match.** A generated "frame B" changes everything at once and ruins a spot-the-difference clue. Derive frame B from the library still with a deterministic pixel edit (`episodes/ep03_the_goose/make_stills.py` removes the goose with a numpy-only harmonic inpaint plus matching grain; OpenCV and SciPy weren't installed). Check it at phone size, under the same look it will be shown in.
- **A derived frame that later episodes replay belongs in the library.** An episode sees only its own `stills/` and the series `stills/`. Episode 3's `yard_gone` was first written to the episode's own folder, where Episodes 4 and 5, which replay that night, would never have found it. It now goes to `stills/`.
- **Placing coordinates by eye failed.** Use `pipeline/grid.py <still> -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]` and read the fractions off the grid. Without `-o` the grid image lands next to the still, in the committed library.
- **Tight boxes.** A mirrored `alter_box` that was too big flipped part of the porch post and left a ghost edge. Keep the box tight to the object.
- **Check roadmap payoffs against the real stills early.** The planned finale ("Deb has two legs; she's been standing on one") contradicts the user's stills, which show Deb on two legs. Plant the stills a payoff needs before it's too late.
- **Build before the images exist.** Every shot lists fallback `views`, and a missing still renders as a labeled placeholder. The first pilot shipped as an animatic with placeholder cards while the images were blocked, so the user could review the edit, the timing and the audio before any image existed.

## Video and file size

- **Film grain is expensive to encode.** The first uncapped render (crf 19) was 245 MB. The master is now crf 21 with `-maxrate 9M -bufsize 18M`. An 80 s master is still about 88 MB.
- **Chat attachments cap at 30 MB.** `pipeline/deliver.py` makes a two-pass copy with light denoise (`hqdn3d`), targeting `--max-mb 29`. Episode 1 came out at 28.9 MB. TikTok re-compresses to about that bitrate anyway.

## Audio and voices

- **You can't listen, so measure.** Every mix decision was checked by numbers, and two problems showed up only in them:
  - Mud: the first score had over a third of its energy below 60 Hz, which masks dialogue. Highpassing (the bed and the master), less drone and cello, and an added violin layer fixed it; stacking more lows would not have.
  - Phone speakers: the first impact was almost all sub, so phones barely played it. A mid body, a noise boom and saturated harmonics fixed it.

  The measured numbers, targets and methods are in `nobody-moves-sound-design` ("Phone speakers and mud", "Measure" and `references/baselines.md`). Measure a new show's episodes against the same targets, not its numbers.
- **One command measures a mix:** `pipeline/build_audio.py episodes/<ep> --stems`, then right away `pipeline/mixcheck.py episodes/<ep>`. It checks loudness, true peak, dialogue over music, the music-out shots and the hits, and exits 1 on a hard failure. `make_episode.sh` rebuilds without stems, so run mixcheck before it, not after.
- **Dialogue buried?** Move the line off the sound or trim `LEVELS` (`nobody-moves-sound-design` recipe d). Don't turn the voices up: they are RMS-matched per line, so louder voices only push the limiter.
- **"More dramatic, more cinematic"** was answered with concrete, measurable changes: 48 kHz stereo, a trailer toolkit (braam, impact, riser, whoosh, string pad, heartbeat, shimmer), an intensity curve toward the climax, `"music": "out"` drops and automatic hits. The listening judgment went back to the user, since the agent couldn't hear it.
- **A crash in `string_pad`:** `ValueError: operands could not be broadcast together` from `pipeline/sounds.py`. `int()` rounding of the last pad segment can leave one sample less room than the segment needs, and it depends on the episode's exact length. Clip the segment before adding it: `seg = (voice * env)[: len(y) - s0]`, then `y[s0: s0 + len(seg)] += seg`. The clip is a no-op for lengths that already work, so existing episodes keep their exact audio. It's fixed in `shows/nobody-moves`, so every copy has it.

## Determinism and regressions

- **Python's `hash()` changes between runs** (PYTHONHASHSEED). `_rng` seeds from `sha256(repr(key))`.
- **A shared RNG made each sound depend on everything generated before it,** so Episode 2's chimes would have differed from Episode 1's. Each sound now seeds its own stream.
- **Global per-kind caches leak between shots.** Episode 2's second doorbell shot reused the first one's frames. Key caches by shot id.
- **A missing optional field crashed the renderer** (`render.py` with no `STILLS` dict). Use `getattr(ep, "STILLS", {})` for optional episode fields. The self-test caught it.
- **Regression check before any pipeline change:** render `--preview` at a dozen fixed times and build the audio, before (via `git stash`) and after. Then `cmp` the PNGs and `soundtrack.wav`, and confirm the voice cache made no new clips. Episode 1 stayed byte-identical through the renderer rewrite. When a change is meant to alter old episodes (like the cinematic redesign), tell the user.

## Writing and runtime

- **Runtimes run long.** Episode 3's draft was 111.37 s and shipped at 88.7 s. The cuts were narration that repeated what the screen already said ("the stamp already says 5:41 AM"), a narration beat folded into a character line, and one whole beat deleted. Trim lines; don't speed up voices. (The pilot was first brought under 90 s by speeding voices up; later episodes cut lines instead.)
- **The caption splitter broke "No. 5" into two captions.** The splitter now skips the abbreviations in `ABBREV` in `render.py`. Add your show's own.
- **"Make the captions bigger and highlight the spoken word."** Kokoro reports no word timings, so `pipeline/words.py` measures them from each finished voice clip: the pauses at punctuation mark the phrases, and phoneme counts share out the time inside each one. At 68 px only about 20 characters fit on a line, so long captions split into two-line chunks. A greedy split left lone words on screen for 0.2 s ("hon.", "before."), so the split is a small cost search: sentence end, then comma, and no lone words, split names or flashes under 0.7 s.
- **"AM" as "A.M." was read as two letters.** The pronunciation engine takes each period as a sentence break. Write abbreviations without periods in the spoken text.
- **Text overflowed** on polaroid labels and board cards. Auto-fit the font size, and shorten the label ("LORRAINE (BETWEEN OUTFITS)" became "LORRAINE (NO BEE)").
- **The preview showed stale labels.** The renderer reads shot fields from `build/timeline.json`, so re-run `build_audio.py` before previewing. Voices are cached, so it takes seconds.

## Editing safely

- **A Python heredoc truncated `build_audio.py`,** because `open(p, 'w')` ran before an exception. It was restored with `git checkout --`. Build the new content fully before opening the file for writing.
- **Text-match edits failed on literal `×` and `·`.** Use the Edit tool for those.
- **For scripted replaces,** `assert s.count(old) == 1` before each one.
- **"Modified since read":** re-read the file before writing.

## Long jobs and safety checks

- **Long renders:** about 5 minutes for 80 s, and about 10 minutes for a full `make_episode.sh`. Run them in the background and watch the log for `wrote|MB|Traceback|Error`.
- **An `rm` with an unresolved path was denied.** Write to a new scratch file instead of deleting.
- **A `git fetch` right after a merge was denied** by the permission classifier. Confirm the merge on GitHub instead.
- **A stop hook demanded commit and push** at the end of turns. Commit finished work on the working branch. Never put model identifiers in commits or PRs, and never commit keys or `.env`.
