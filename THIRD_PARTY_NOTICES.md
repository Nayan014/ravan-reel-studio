# Credits and third-party notices

**Ravan Reel Studio is built by Techno Ravan using Vibha Ramprakash’s original open-source video effects engine.** The MIT licence at the repository root covers original project contributions. It does not replace any component's copyright, licence, asset terms or trademark rights.

| Component | Contribution and preserved notices |
| --- | --- |
| [Vibha Ramprakash / claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects) | Original effects engine, effects and bundled resources. MIT notice: [skills/effects/LICENSE](skills/effects/LICENSE). Imported revision and original hashes: [SOURCE.json](SOURCE.json). Local adaptations are recorded separately. |
| Techno Ravan | Guided agent workflows, reel planning, review/approval integration, local dashboard adaptations, source-quality pipeline and packaging. |
| Synthetic dashboard demo | Generated colour cards, labels and quiet test tones in `examples/demo/`, by Techno Ravan under the project MIT licence. Uses the bundled Inter font with its preserved notice. Contains no personal footage or recorded voice. |
| [Nayan V. / Techno Reel](https://github.com/Nayan014/techno-reel) | Adapted dashboard and bundled legacy Remotion kit. Preserve [dashboard/LICENSE](dashboard/LICENSE), [renderer licence](tools/techno-reel/LICENSE), [import record](tools/techno-reel/STUDIO_SOURCE.json) and [renderer third-party notices](tools/techno-reel/THIRD_PARTY_NOTICES.md). |
| [HeyGen / Hyperframes](https://github.com/heygen-com/hyperframes) | HTML-based finishing and Studio. Installed from pinned npm dependency 0.9.30 under Apache-2.0; its package and transitive dependency notices apply after installation. See [local integration](tools/hyperframes/README.md). |
| [Nafay 3D — AI Video Editor](https://nafay3d.com/) | Seven motion-graphics styles, standalone editor, fonts and synthesized sound kit. [YouTube](https://www.youtube.com/@nafay3d), [import/adaptation record](tools/nafay-video-editor/STUDIO_SOURCE.json), [integration notice](tools/nafay-video-editor/STUDIO_INTEGRATION.md) and [font metadata](tools/nafay-video-editor/FONT_NOTICES.md). No explicit package licence was supplied. Bundled at the repository owner’s request, outside the project MIT grant. |
| [SYSTRAN / faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Local CPU transcription, installed separately under MIT. CTranslate2, PyAV and speech-model weights keep their own terms. Model downloads are not part of the project MIT grant. |
| Music and sound effects | Four music tracks and 23 SFX from the imported kit. Stable IDs, authors, URLs and recorded CC0 notices: [catalogue](assets/audio/catalogue.json) and [original credits](tools/techno-reel/public/sfx/CREDITS.md). |
| Fonts | Font-specific notices are preserved beside the font files in [effects fonts](skills/effects/fonts/) and [renderer fonts](tools/techno-reel/public/fonts/). These terms are separate from the application licence. |
| Tracking models | YuNet and MediaPipe Selfie Segmenter sources and notices: [models/NOTICE.md](skills/effects/models/NOTICE.md). Their original MIT/Apache-2.0 terms apply. |
| Remotion and other dependencies | Retain their installed licences, including Remotion's usage terms. The legacy kit's MIT licence is not a licence to all its dependencies. See its [third-party inventory](tools/techno-reel/THIRD_PARTY_NOTICES.md). |

Upstream author credits and imported-file hashes are preserved even where local wrappers, documentation or render integrations have changed. Existing upstream examples are identified as examples; they do not authorize cloning another person's voice. Personal recordings and project-specific documents are excluded from the public package.
