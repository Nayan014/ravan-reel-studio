---
name: wf
description: Route this project's workflow commands when the user invokes wf, /wf, /WF, or asks for the workflow menu. Route single-video edits, combined recorded reels, effects, gallery and resume requests without changing their approval requirements.
---

# Workflow commands

For every question and approval, follow `../../docs/WORKFLOW_REVIEW.md`: use native choice buttons and open interactive HTML reviews with script, scene and frame feedback. Read saved submissions on resume; preserve the existing actual-frame approval gates.

This is a small command menu and router. Keep the editing procedures in their existing skills. Resolve the studio root from this canonical `skills/wf/` directory, two directories above it. Read the studio's `AGENTS.md` for the local skill index.

Use the user's invocation and any host supplied trailing arguments. Normalize the prefix and subcommand to lowercase; preserve filenames, user text and other arguments exactly. The native command name is lowercase `wf`. Treat an uppercase `/WF` as an alias when the host passes it to the agent.

## Command menu

For bare `/wf`, `/wf help`, `/wf commands`, or an unknown subcommand, show this numbered menu and wait. If the host supports selectable replies, offer the same six choices as selectable options. Otherwise ask the user to reply with a number or an action name. Do not start an edit, create a session or render anything just by showing the menu.

| Pick | Shortcut | What it does |
| --- | --- | --- |
| 1 | `/wf-video` | Guided edit with recent videos, sample choices and approval of actual frames before rendering |
| 2 | `/wf-gallery` | Show all 51 effect samples and three bonus looks |
| 3 | `/wf-effects` | Use a named effect directly |
| 4 | `/wf-resume` | Continue a saved guided edit |
| 5 | `/wf-reel` | Combine numbered takes with Vibha effects and Hyperframes finishing |
| 6 | `/wf-reel-plan` | Choose an idea, approve the script, then record and attach takes |

Keep the space based forms `/wf video-edit`, `/wf gallery`, `/wf effects <details>` and `/wf resume <session>` as aliases. The original `/video-edit` and `/effects <details>` also remain available. The standalone shortcut skills let a host suggest whole command names when the user filters the command menu with `/wf-`; do not claim autocomplete for arbitrary words after a space.

Map 1 to video-edit, 2 to gallery, 3 to effects, 4 to resume, 5 to reel and 6 to reel-plan. An explicit `/wf 1` through `/wf 6` uses that mapping. Accept a bare numeric or action-name reply only while this workflow menu is the pending question. Never intercept numbers belonging to a video picker, effect gallery choice, preview approval or another active workflow stage. Forward any remaining user details to the chosen route. `/wf reel` aliases `/wf-reel`; preserve all earlier command forms.

Mention that every effect name and bonus look from `../effects/SKILL.md` remains usable through the effects route. Do not flood the menu with all 51 names. The old plain language command `Start video edit` also remains an alias.

## Routes

- `reel-plan`: Read `../wf-reel-plan/SKILL.md`. `/wf reel-plan` aliases `/wf-reel-plan`; develop an idea into an approved saved shooting plan, then attach recordings and continue reel.

- `reel`: Read `../wf-reel/SKILL.md`. Handle numbered-take folders, HTML plan review, visual selection and actual combined preview approval through its helper. An existing project slug resumes its status; do not start it over.
- `video-edit`: Read `../video-edit/SKILL.md` and follow it, preserving any user notes after the subcommand. Begin at its video selection stage. Wait for each choice and for explicit approval of actual preview frames before rendering. Do not ask the user to invoke another command to continue.
- `effects`: Read `../effects/SKILL.md` and handle the trailing effect request as a direct effects request. For example, `/wf effects orbit from 3 to 6 seconds` forwards `orbit from 3 to 6 seconds`. If the clip or effect is missing, ask for it using that skill's workflow. Do not replace or rename the existing effects.
- `gallery`: Display `docs/effect-gallery/effects-1.jpg` through `effects-6.jpg` using the host's image display capability. These are dummy reference samples, not the user's actual frames. Label them with their catalogue numbers and offer the illustrated PDF. Do not create a session or start rendering.
- `resume`: Read `../video-edit/SKILL.md`. Run its helper's `status --session ID`, then continue the pending stage using the saved session rather than starting again. If the session needs sample selection, show its samples. If it needs preview approval, show its actual saved frames and plan and ask for approval. An approved plan may render only if the helper still accepts its recorded approval. If already rendered, return the saved video path. If no session identifier was provided, ask for one.

## Discovery

This skill is exposed through project links under `.agents/skills/wf` and `.claude/skills/wf`; Gemini CLI also has a project command entry under `.gemini/commands/wf.toml`. Use `/wf` in hosts that expose the skill or custom command. If a host does not offer it, the same route can be invoked as plain text such as `Use the wf skill with video-edit` or the host's skill mention, such as `$wf video-edit`. Do not claim a native command was tested in another app unless it actually was.
