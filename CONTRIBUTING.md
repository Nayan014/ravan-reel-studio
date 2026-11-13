# Contributing to Ravan Reel Studio

Start with [README.md](README.md) and [setup](docs/SETUP.md). `npm start` prepares the runtime and opens the demo; use `npm start -- --no-open` for headless checks. Preserve original recordings, approved scripts, saved projects and upstream notices. Keep media generation and final-export approvals explicit; do not bypass fingerprints or pending-feedback checks.

## Checks

The dashboard tests require only Node 22.18+:

```bash
npm run test:dashboard
```

After effects/reel setup, run the Python suite:

```bash
skills/effects/.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Local-browser integration tests use synthetic media, ffmpeg and the pinned Hyperframes runtime. They include actual encoded 4K/60, 4K/30, 1080p/60, fractional rates, rotation, crop, audio synchronization and effect-cache reuse:

```bash
REEL_INTEGRATION=1 skills/effects/.venv/bin/python -m unittest discover -s tests -p test_reel_pipeline_integration.py
```

Integration fixtures are short technical checks, not laptop-performance benchmarks. The shared effects environment must exist. Some legacy compatibility checks also need the optional Remotion dependencies. Windows/Linux results should be labelled unverified until run on those platforms.

## A clean publication copy

The portable studio's contents become the repository root; do not publish the surrounding personal workspace. This checkout can contain private local files. Create a separate publication copy:

```bash
python3 scripts/package_release.py --output outputs/releases/ravan-reel-studio
```

Use Python 3.10+. The destination must not exist. The packager copies public source/resources, preserves only safe relative discovery links, creates empty input/output placeholders, and writes `PUBLICATION_MANIFEST.json` with SHA-256 hashes. It excludes recordings, exports, environments, caches, credentials and personal documents. Local originals are never moved or deleted. Review the manifest before adding a Git remote. Never upload an acceptance-test folder after installing environments or creating test media inside it.

Do not commit `.env` files, API keys, recordings, generated projects or virtual environments. The publication helper and `.gitignore` are guardrails, not a guarantee against secrets embedded in source text. Inspect the intended files. GitHub URL, repository initialization, commits and pushing are separate steps once the owner supplies the destination.

Videos and audio outside the usual input/output folders are also excluded. The only public video exception is `examples/demo/export/demo.mp4`, generated from colour cards and test tones by `examples/generate_demo.py`. Credited music, sound effects and upstream example audio retain explicit public exceptions. Do not add broad exceptions for `inputs/` or `outputs/`. `npm run demo` copies the synthetic example into ignored outputs without requiring rendering tools or overwriting a project.

## Changes and attribution

Document behavior and setup changes. Run the focused checks for the affected path; UI changes should be checked at desktop and narrow widths. Keep sample media synthetic or demonstrably licensed. Preserve Vibha's engine credit, Techno Reel dashboard/renderer notices, Hyperframes attribution and each bundled asset's licence. Update `SOURCE.json` local adaptations without rewriting imported upstream hashes.
