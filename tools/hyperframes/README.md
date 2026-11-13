# Hyperframes integration for Ravan Reel Studio

Pinned Hyperframes 0.9.30 supplies HTML captions, Studio editing and final assembly. Install from the repository root:

```bash
npm --prefix tools/hyperframes ci
node tools/hyperframes/hyperframes.mjs browser ensure
```

Run commands with an explicit composition directory:

```bash
node tools/hyperframes/hyperframes.mjs check /absolute/project/hyperframes --json
node tools/hyperframes/hyperframes.mjs snapshot /absolute/project/hyperframes --review
node tools/hyperframes/hyperframes.mjs render /absolute/project/hyperframes --quality delivery --fps 60000/1001 --workers 1 --experimental-fast-capture=false --output /absolute/project/export/final.mp4
```

Use the approved output profile rather than a fixed 30 FPS. The reel workflow supplies the exact width, height and rate, mutes source-video audio, and carries one authoritative source-voice track.

The wrapper keeps runtime/config caches in this tool folder, disables telemetry/update checks and uses installed Google Chrome on macOS when available. Otherwise use `browser ensure`, or set `HYPERFRAMES_BROWSER_PATH` to an installed compatible executable. Node 22.18+ and system ffmpeg/ffprobe are required. Runtime dependencies and downloaded browsers are not included in the publication copy.

A targeted `undici` override to 7.30.1 fixes advisories in the upstream pinned dependency without changing Hyperframes 0.9.30. The [upstream advisory](https://github.com/advisories/GHSA-2m5v-pch6-74hx) identifies the patched 7.x version. Recheck with `npm --prefix tools/hyperframes audit` when updating; passing an audit is not a guarantee of complete security.

Source: [HeyGen / Hyperframes](https://github.com/heygen-com/hyperframes), Apache-2.0. Installed skills and render-contract references live under `node_modules/hyperframes/dist/skills/`. Preserve dependency notices. Existing authored projects and the bundled Remotion renderer remain separate.
