---
name: wf-video
description: Shortcut for /wf video-edit when the user invokes wf-video or /wf-video. Start the guided video edit with approval of actual preview frames.
---

# Start the guided video edit with approval of actual preview frames

Read `../wf/SKILL.md` and handle this invocation as `/wf video-edit`, preserving any user supplied trailing arguments. Follow that route immediately rather than asking the user to invoke a different command. Inherit its existing selection and approval requirements. Resolve the studio root two directories above this canonical skill folder.
