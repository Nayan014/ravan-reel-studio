---
name: sound-design
description: Choose documented CC0 background music and sound effects for the studio's Reel and YouTube workflows and review the full mix by scene.
---

# Sound design

New plans inherit the music chosen in Studio Settings → Audio & Sound. Start with that track, including silence when selected. Offer scene-based alternatives during project review and apply the creator’s choice.

Use the studio's `assets/audio/catalogue.json`. For a new selection, use a CC0 recording with its creator, license URL and recording-level, dated download or favorite count. Pack totals are labeled separately for existing projects. When adding a recording, check the exact source listing and retain its displayed count, metric, source and check date. Keep older IDs stable.

Choose by the moment the viewer should hear. Try `music-bubbles` under a bright demo, `music-chill` under an explanation, and one `sfx-pop-1` on a reveal. Leave a scene quiet when the words carry it. In the project plan set `audio.recommended_music` and `audio.music` to the chosen ID (or null), and place cues in `audio.sfx` with scene ID, sound ID, seconds from scene start and gain. For a reveal at 12 seconds in a scene starting at 5 seconds, use `{"scene":"02","sound":"sfx-pop-1","at":7.0,"gain":0.15}`. Retain `audio.selection_policy: "verified-recording"` for new projects and sound selections. Start with the existing 0.10 music gain and listen under dialogue.

Use the interactive frame review to play the full mix or an individual scene, including late cues. Lower distracting accents or use No background music. A change to the selected audio needs current frame/audio approval before export.
