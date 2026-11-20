---
name: natural-narration
description: Audition and select free local English Kokoro narration for silent demos or fully narrated Reels and YouTube videos. Preserve recorded dialogue and time captions to the chosen performance.
---

# Natural narration

The creator can listen to the local Kokoro presets in Studio Settings → Audio & Sound. New projects save the selected preset in `audio.narration_voice` and use it for both readings unless the creator requests a different voice.

Start in `/wf-reel-plan` or `/wf-video-plan` and use its attach, analyze and review steps. Attach footage for each scene, including silent B-roll for a fully narrated video. Keep existing spoken takes. For a speech-free scene, use the English script already in the plan or supply its line.

Run commands from the studio with its effects Python. The worker uses the installed VoiceStudio MLX environment on Apple Silicon and the cached `mlx-community/Kokoro-82M-bf16` weights. The bundled checkout is `tools/techno-reel/voicestudio`. The installer and audition helper also recognize an existing VoiceStudio checkout. To choose another checkout, use `export VOICESTUDIO_DIR="/path/to/VoiceStudio"`. For first-time setup on Apple Silicon, run `npm --prefix tools/techno-reel run setup`. Download Kokoro and the selected English presets there before auditioning. Synthesis runs offline with direct Kokoro word timings. The upstream project had 10,211 GitHub stars on 2026-11-18. [Repository](https://github.com/hexgrad/kokoro) · [Apache 2.0 model](https://huggingface.co/hexgrad/Kokoro-82M)

```sh
skills/effects/.venv/bin/python scripts/reel_workflow.py audition --kind reels --project SLUG --scene 02 --line "Watch the build finish."
node scripts/review.mjs prepare --kind reels --id SLUG --stage plan --document outputs/reels/SLUG/review.html
```

Use `--kind videos` for YouTube. Listen before using `--confirm-no-speech` on a clip with ambient sound. This option replaces that scene's ambient audio with the voiceover. Start the dashboard with `npm run dashboard` and open the returned review URL so the creator can play A and B and choose a reading. If both sound mechanical, revise the delivery or use the creator's recorded take. Match the voice across scenes.

With `--delivery FILE`, override either reading. Phrase text must add up to the exact caption line. Use a slower phrase for emphasis, a short pause between phrases, and a spoken alias for a difficult name. For example, for “Open the API. Watch the build finish.” use:

```json
{"B":{"speed":0.96,"phrases":[{"text":"Open the API.","pronounce":{"API.":"A P I."},"pause_after":0.18},{"text":"Watch the build finish.","speed":0.93}]}}
```

The reading buttons attach the exact audition. If processing a choice made through scene feedback, call `select-voice --kind KIND --project SLUG --scene ID --audition-id CURRENT_ID --take B`. To use a supplied recording instead, call `select-voice --kind KIND --project SLUG --scene ID --recording PATH`, listen and confirm the transcribed words and captions. Fit the complete performance within the footage. Preview every voiced scene in its final mix and collect the usual approval.
