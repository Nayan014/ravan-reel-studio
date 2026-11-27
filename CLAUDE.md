# Ravan Reel Studio

Read `AGENTS.md` in this folder for the shared skill index and workflow. See `AI_SKILLS.md` for the central `ai-brain` skill catalog (fetched automatically; run `python3 scripts/ai_brain.py` if `.claude/skills` is empty) and instructions on adding new skills. For `Start video edit` or `/video-edit`, follow `skills/video-edit/SKILL.md`; it guides selection and waits for approval of actual frames before rendering. For a direct effect request, use `skills/effects/SKILL.md`. Use the local renderer and runtime. This project is usable without a global Claude skill installation.

Use `skills/wf/SKILL.md` for `/wf`, including `/wf video-edit`. Bare `/wf` shows the local command menu.

Use `/wf-reel-plan` for a portrait reel or `/wf-video-plan` for a landscape YouTube video, starting from an idea, footage or a saved project. Both continue through review and export. `/wf-video` remains the quick single-video editor.
