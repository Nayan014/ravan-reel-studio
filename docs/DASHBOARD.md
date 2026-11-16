# Review your projects

For automatic dependency setup, demo installation and browser opening, run `npm start` from the repository root. To browse existing work without installing production dependencies, run:

```bash
npm run dashboard
```

Open [Ravan Reel Studio](http://127.0.0.1:4173). Stop the server with **Ctrl+C** in its terminal.
For a safe example, run `npm run demo` in another terminal. The pre-rendered synthetic video, cover and posting copy appear automatically; personal footage is not used.
The dashboard needs **Node 22.18 or newer**. It uses built-in Node libraries: no `npm install`,
Python, ffmpeg, voice engine, or Remotion setup is needed for viewing existing work.

If another dashboard is using the default port, set `DASHBOARD_PORT` before starting.
For example, on macOS/Linux:

```bash
DASHBOARD_PORT=4174 npm run dashboard
```

In PowerShell: `$env:DASHBOARD_PORT=4174; npm run dashboard`.
Use the `http://127.0.0.1:<port>` address printed in the terminal; `localhost` and LAN addresses
are intentionally not accepted. The server stays on this device.

## Your library

The dashboard discovers **Reels** in `outputs/reels/` and **Edits** in `outputs/edits/`.
Export packages with videos but no workflow plan also appear. Use search and the All / Reels /
Edits filters to find a project. Data refreshes every five seconds. Search, selected tabs,
export selection, and playing videos are preserved during refresh.

Each project has five sections:

- **Overview:** recorded or latest available export, cover, social copy, and saved workflow records.
- **Plan:** sandboxed HTML plans and frame reviews, plus saved JSON plans where available.
- **Previews:** actual recorded preview frames, or discovered preview images when no record exists.
- **Exports:** video variants and covers to reveal in their folders, plus social captions to copy or download.
- **Files:** original recordings and supporting plans, media, and review records.

Use **Open project folder** to open the project folder on the computer running the server.
**Show video in folder** and **Show cover in folder** open the selected media's own location,
so you can copy the original file directly. On macOS, Finder selects the exact file; Windows
and Linux open its containing folder. Choosing another video export updates its file-location
button. The Exports tab offers the same action for every listed video and cover.
**Copy folder path** copies the portable, studio-relative project path. Other file download
controls retain the original filename.
Browsers may not play every source codec; the original file is still available for download.

## How files are selected

`export.json` and an edit's `session.json` take priority when identifying the video. If no usable
record exists, the newest video directly inside `export/`, `renders/`, or the package root is
selected. Other exports remain available in the video selector and Exports tab.

Cover paths recorded in `export.json` take priority. Otherwise the dashboard discovers images
with `cover` or `thumbnail` in their filename, preferring PNGs. Source images and contact sheets
are excluded from automatic cover selection. Social copy is read from Markdown or text files
whose name includes `caption` or `Social_Copy`, including files in `publishing/`. Platform and
title/description headings become separate copyable fields; hashtags stay in the text.

Social caption fields start collapsed in Overview and Exports. Click a label to expand its text and Copy button. An expanded field stays open during library refreshes on the same project tab. New posting copy defaults to Instagram, YouTube title/description, TikTok and LinkedIn; see [SOCIAL_COPY.md](SOCIAL_COPY.md) for the file format and writing preferences.

Files are read in place. Project media, raw footage, assets, working files, previews, exports,
and publishing files are indexed; hidden folders, runtime dependencies, models, and composition
source folders are omitted from the file browser. Missing files and malformed metadata produce
warnings without breaking the rest of the library. The dashboard does not create missing assets.

## Saved records and approvals

**Export available** means a video exists. It does not mean it passed review. Saved approvals,
checks, and export metadata are displayed as historical records; the dashboard does not rerun
validation or certify that those records match the current files.

Creation, effects, and rendering stay with the editing agent. The interactive review page accepts script, scene and individual frame feedback, music selection and explicit stage-specific approval. Direct visual editing uses Hyperframes Studio. The agent processes these submissions through the existing workflow checks. The dashboard has no AI access, settings editor, media uploads, or publish action. See [Clickable workflow reviews](WORKFLOW_REVIEW.md).

## Development and credits

Run the focused discovery, HTTP/media, caption, and security tests with:

```bash
npm run test:dashboard
```

The dashboard's layout and server patterns are adapted from
[Techno Reel](https://github.com/Nayan014/techno-reel) by Nayan V. Its MIT notice is preserved
in `dashboard/LICENSE`. Effects originate from
[Vibha Ramprakash's video effects](https://github.com/Vibha-Ramprakash/claude-video-effects),
with the existing notices in `skills/effects/LICENSE` and `SOURCE.json`.
This dashboard does not change the licences of the renderers, media, fonts, or dependencies.

The studio dashboard is separate from the bundled renderer dashboard. Existing workflow formats,
render code, original footage, and approval files are not changed by browsing.

## YouTube videos

The Videos filter discovers planned and exported YouTube projects under `outputs/videos/`. Plans, feedback, actual preview frames, music auditions, native Hyperframes Studio and downloads follow the same review stages as reels. Start with `/wf-video-plan`; use `/wf-reel-plan` for reels. The quick single-video editor remains `/wf-video`.

## Reference style notes

A selected reference appears as a saved style record and in production review summaries. Its pinned profile and readable notes are available in project supporting files. Original reference videos remain in the private root references/ folder.

## Nafay projects

Standalone Nafay edits use renderer nafay under outputs/videos/. The Videos category shows their source, plans, actual frame reviews, voice/effects preview, exports and cover. They use Nafay's graphics editor in chat. Hyperframes Studio is available for Hyperframes projects.
