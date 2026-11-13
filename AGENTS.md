# Shared instructions for this workspace

This folder is a portable video effects workspace. Use its local skill packages and assets. Resolve paths from this folder or the relevant `SKILL.md`; do not rely on the original Codex installation or a previous chat.

For reel scripts, storyboards and production plans, first read `docs/REEL_PLAN_FORMAT.md`. It records the user's reusable preferences. Create HTML for review before any PDF, with the full script followed by one integrated scene table. Update that preference file when the user changes the shared format. These planning defaults do not replace the guided workflow's effect selection or actual-frame approval requirements.

## Clickable questions and plan editing

Read `docs/WORKFLOW_REVIEW.md` for all workflow questions, choices and approvals. Use native choice buttons when available. Open plans through the interactive review page so users can submit script, scene and frame feedback and approve the exact review revision. Preserve actual-frame approval gates.

## Available skills

| Skill | When to use it | Instructions |
| --- | --- | --- |
| wf | `/wf` menu and routes for video-edit, effects, gallery and saved sessions | `skills/wf/SKILL.md` |
| wf-nafay | Standalone Nafay 3D video editing with seven landscape graphics styles and studio approvals | `skills/wf-nafay/SKILL.md` |
| wf-video | Standalone shortcut for the guided edit | `skills/wf-video/SKILL.md` |
| wf-reel-plan | Create a portrait reel from an idea, footage or saved project through final export | `skills/wf-reel-plan/SKILL.md` |
| wf-video-plan | Create a landscape YouTube video from an idea, footage or saved project through final export | `skills/wf-video-plan/SKILL.md` |
| wf-gallery | Standalone shortcut for sample pictures | `skills/wf-gallery/SKILL.md` |
| wf-effects | Standalone shortcut for named effects | `skills/wf-effects/SKILL.md` |
| wf-resume | Standalone shortcut for a saved session | `skills/wf-resume/SKILL.md` |
| video-edit | Start a guided edit, choose from the three newest inputs, get effect recommendations with sample images, review actual frames and approve rendering | `skills/video-edit/SKILL.md` |
| effects | Add or choose talking head video effects, animated text, graphic cards, camera movements or colour treatments | `skills/effects/SKILL.md` |

For `/wf` commands, read `skills/wf/SKILL.md` and route there. Bare `/wf` shows a menu; `/wf video-edit` starts the guided workflow. For `Start video edit` or `/video-edit`, follow the video-edit skill directly. Its sample choice, actual preview review and final approval are separate user decisions. Use its helper to render only the approved plan. Direct effect requests can use the effects skill. For a visual choice, open `docs/Video_Effects_Visual_Guide.pdf` or inspect the appropriate image listed in `skills/effects/references/catalogue.json`. That JSON uses preview paths relative to `skills/effects/` and contains all 51 effects and three bonus looks.

`/wf-video`, `/wf-gallery`, `/wf-effects` and `/wf-resume` retain their existing quick-edit routes. `/wf-reel-plan` and `/wf reel-plan` create portrait reels; `/wf-video-plan` and `/wf video-plan` create landscape YouTube videos. Both planning commands offer an idea, three suggestions, existing footage or a saved project, and continue through final production. `/wf-reel` and `/wf reel` are retired public commands. The numbered menu preserves choices 1–4, with 5 for Reel Plan and 6 for YouTube Video Plan. Apply menu numbers only while that menu is pending. Read shared production instructions in `skills/wf-reel-plan/references/production.md`.

## Working on a video

- For the local review dashboard, run `npm run dashboard` from this folder and open `http://127.0.0.1:4173`. See `docs/DASHBOARD.md`. It discovers reels, YouTube videos and edits. Interactive review pages accept feedback and stage-specific approvals for the agent to process. Viewing needs only Node 22.18+, without renderer setup.
- Use the actual source video and user supplied assets. `inputs/` is available for local media; an external source path also works.
- Run the local skill setup if its environment is missing. Use `skills/effects/.venv/bin/python` on macOS/Linux or `skills/effects/.venv/Scripts/python.exe` on Windows.
- Save plans, check frames and renders in `outputs/` by default. Respect a different destination if the user gives one. Keep the original video intact.
- Inspect check frames before a full render. Correct face overlaps, unreadable copy, edge clipping and demo values. Use the user's actual words, handles and metrics.
- The skill adds visuals and carries the source audio into the export. Silence removal, new sound design and captions are separate tasks. `wave-trim` only animates a waveform.
- Report the output file path and ask the user to watch the result before posting.

For new skills, add their complete package under `skills/` and update the index above. Do not introduce a dependency on a particular provider or a home directory installation.

## Reference styles

Both planning commands use `skills/wf-reel-plan/references/reference-style.md` once footage is imported/attached. Offer reference filenames from root `references/` only when videos exist and no project choice is saved. Skip idea/script preparation for supplied footage. Reuse content-hashed analysis and pinned project style notes. The reference library is private and stays out of Git/public packaging.

## Nafay standalone editor

`/wf-nafay` and `/wf nafay` use `skills/wf-nafay/SKILL.md`. New `/wf-video` runs offer Vibha effects or Nafay motion graphics; existing sessions resume their editor. Nafay projects use outputs/videos/ and renderer nafay. Its seven creator-labelled styles are in assets/styles/nafay.json for YouTube planning. The original package lives under tools/nafay-video-editor/. Use the studio wrapper and local setup, preserving cut, plan and actual-frame/audio approvals. Mixed rendering is deferred.
