# Channel setup: TikTok, Instagram, YouTube

One name, one handle and one profile picture on all three apps. The profile picture is the show's title, not a character, so it outlives a season's cast. The YouTube banner shows the season's witnesses and changes each season. The bios describe the format, and only the YouTube description tells the season's story.

Make the art with `.venv/bin/python channel/make_channel_art.py`, run from `shows/nobody-moves/`. Add `--preview` to also write `channel/build/`, which shows each file at the sizes the apps display it.

| File | Where it goes |
|---|---|
| `art/avatar.png` (1080×1080) | Profile picture on TikTok, Instagram and YouTube |
| `art/youtube_banner.jpg` (2560×1440, 1.6 MB) | YouTube banner |
| `art/avatar_dark.png` | Alternative profile picture. Not recommended: a black circle vanishes on dark-mode apps |

## Name and handle

- **Name:** `NOBODY MOVES` on TikTok and YouTube. On Instagram, use `NOBODY MOVES | true crime`, because Instagram searches the name field.
- **Handle:** `@nobodymoves` everywhere. If it's taken on any app, use the same fallback on all three: `@nobodymoves.case`, `@nobodymovescase` or `@watchnobodymoves`. All three apps allow these characters.
- Search each app for "nobody moves" before you claim the handle.

## Profile picture

The black title on the show's yellow is the same yellow as the caption highlight, the exhibit tags and the end card's next-episode line. In TikTok's dark feed, the picture is about 48 px wide beside the follow button, and a yellow circle is the one thing that stands out there. `--preview` shows Lorraine as a season 1 option. A character reads well at 110 px but not at 48, and it would have to change with the cast.

Upload the 1080 file everywhere. The apps display it smaller: YouTube recommends 800×800, and Instagram stores it at 320×320.

## TikTok

TikTok has no banner. The profile grid is the cover: pick a cover frame for every video so the grid reads in episode order.

**Bio.** TikTok is rolling out a longer limit, so write to the old 80 characters:

```
True crime. Every witness is a lawn ornament.
Written by [NAME] · Ep 1 📌
```

This fits 80 characters with a name up to about 13 characters. For a longer name, write `By [NAME]`. Write "written by", not "voiced by": the voices are Kokoro.

- **Pinned videos (up to 3):** Episode 1, the latest episode, and the best Confessional.
- **Link:** personal accounts get the website field at 1,000 followers. Then link the YouTube Season 1 playlist.
- **Playlists,** if your account has them: "Season 1" in order, and "Confessionals".
- **AI label:** turn on "AI-generated content" on every post.

## Instagram

**Name field:** `NOBODY MOVES | true crime`

**Bio** (150 max; this is 129 plus your name):

```
A true-crime docuseries. Every witness is a lawn ornament.
Season 1: somebody moved the flamingo.
Written by [NAME] · Start with Ep 1 ↓
```

Change line 2 each season; the other lines stay.

- **Pinned (up to 3):**
  - Episode 1;
  - the latest episode;
  - an "evidence locker" carousel of the doorbell frames, before and after, so rewatchers can check their theories.
- **Grid:** the profile grid crops each Reel's cover to 3:4, cutting 240 px from the top and the bottom. The title card frame keeps its title inside that crop.
- **Highlights:** optional until you post Stories. Then use "Start here", "Evidence" and "Confessionals".
- **Links:** up to 5. Put the YouTube playlist first and TikTok second.
- **Category:** Video creator.
- **AI label:** turn on "AI info" on every Reel.

## YouTube

- **Banner:** `art/youtube_banner.jpg`.
  - Every device shows only the middle band (y 508–931). A phone shows the middle 1546 px of it: Garrison, the title card and Deb. A computer shows the whole band, all six witnesses. Only a TV shows the cork above and below.
  - `channel/build/preview_banner.png` marks each area.
  - The file limit is 6 MB.
- **Profile picture:** `art/avatar.png`.
- **Description** (1,000 max, this is about 800). The second paragraph is the season; rewrite it when the case changes:

```
NOBODY MOVES is a true-crime docuseries about one suburban yard, where every witness is a lawn ornament. They saw everything. None of them can move.

On June 14th, at 3:12 AM, somebody moved the flamingo three feet to the left. The garden gnome was facing the other way. The porch goose can't go anywhere, she's concrete. The birdbath is representing himself. The wind chime only talks when it's windy, and the solar frog only remembers back to his last full charge.

Every episode ends on a doorbell-cam frame where something has changed. Find it, then comment the object and the timestamp.

New case files every week, plus Confessionals: one ornament, one grudge, under 30 seconds. Start with Episode 1 in the Season 1 playlist.

Written by [NAME]. Reenactments dramatized with AI. The flamingo is real.
```

- **Keywords** (Studio → Settings → Channel): `true crime parody, mockumentary, lawn ornaments, garden gnome, pink flamingo, comedy series, doorbell camera, mystery`.
- **Links:** TikTok and Instagram. The first link shows on the channel page.
- **Playlists:**
  - "Season 1: 7 Birchwood Court", in episode order;
  - "Confessionals".
  - Show Season 1 first on the channel home.
- **AI label:** on every Short, answer yes to "altered or synthetic content" in Studio.

## A new season

Keep the name, the handle, the profile picture, and the TikTok and Instagram bios except Instagram's line 2.

Change:
- In `make_channel_art.py`: `BANNER_POLAROIDS` (the new witnesses; the two nearest the card are the ones a phone shows) and `CASE_LINE`. Then re-run it and upload the new banner.
- Instagram's line 2.
- The second paragraph of the YouTube description.
- A new playlist on each app.

The specs above were current in September 2026. Check them on a phone after the first upload.
