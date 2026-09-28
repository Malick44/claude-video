# Art choices and dimensions

Preview all variants in the [`launch contact sheet`](launch_contact_sheet.jpg). The **title avatar + clue cover/banner** is the recommended launch set. The character/witness alternatives let a later post test whether the cast draws more attention than the puzzle. Every image is generated from the show's existing still library and can be rebuilt with:

```bash
shows/nobody-moves/.venv/bin/python shows/nobody-moves/channel/make_launch_art.py --preview
```

Run that command from the repository root. It writes upload-ready images into each platform's `art/` directory and refreshes the contact sheet. Do not run `make_channel_art.py` unless intentionally changing the original shared brand art.

| Platform | File | Pixels | Use |
|---|---|---:|---|
| All three | `avatar_title.png` | 1080×1080 | Recommended yellow/black profile image; same artwork in each platform folder |
| All three | `avatar_character.png` | 1080×1080 | Lorraine close-up; alternate for a character-led profile test |
| TikTok | `cover_clue.jpg`, `cover_witnesses.jpg` | 1080×1920 | Video cover options for Case 001 |
| Facebook | `cover_clue.jpg`, `cover_witnesses.jpg` | 1640×624 | Wide Page cover options; inspect the live mobile crop |
| Facebook | `reel_cover_clue.jpg`, `reel_cover_witnesses.jpg` | 1080×1920 | Reel poster/cover options |
| YouTube | `banner_clue.jpg`, `banner_witnesses.jpg` | 2560×1440 | Channel banner options; title copy is in the center safe region |
| YouTube | `cover_clue.jpg`, `cover_witnesses.jpg` | 1080×1920 | Custom Short thumbnail options for a verified account in desktop Studio |
| YouTube | `watermark.png` | 300×300 | Optional small video watermark |

The clue visuals ask `WHO MOVED THE FLAMINGO?` without revealing the second change. The witness visuals introduce Garrison/Lorraine. The wide Facebook and YouTube variants are different compositions made for their respective crops; do not interchange them. All images are below the current official YouTube art file-size limits cited in [`PLATFORM_REFERENCES.md`](PLATFORM_REFERENCES.md).
