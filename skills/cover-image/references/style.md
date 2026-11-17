# Techno Ravan cover style

Version: **1.4**  
Status: **Headline-first layout accepted; warm palette pending visual review**  
Direction: **Understated editorial**

The user chose option A (headline first) and requested colours and graphics that feel intentionally designed rather than a stereotypical AI aesthetic. Use restrained contrast, typography and relevant imagery. Do not describe an aesthetic as proof of human authorship; these covers are composed with local code.

## Shared identity

| Element | Current value |
| --- | --- |
| Background | Warm off-white `#F3EFE7` |
| Headline | Charcoal `#252525`, bold and upright, including the final line |
| Topic artwork | Muted stone `#C9C3B8` with a restrained dark outline `#55574F` |
| Headline font | Bundled `skills/effects/fonts/ArchivoBlack-Regular.ttf` |
| Brand font | Bundled `skills/effects/fonts/SpaceMono-Bold.ttf` |
| Brand label | `TECHNO` in orange `#FF9933`, `RAVAN` in red `#EF3340` |
| Brand spacing | One baseline, gap 0.25× the brand font size (9px at 36px); normal letter spacing within TECHNO |
| Rendering | Local code; flat topic artwork, no glow, technical grid or glossy extrusion by default |

Orange TECHNO represents spirituality and red RAVAN represents evil in the creator's brand symbolism. Retain these two brand colours in portrait and landscape, with or without a photo. Do not recolour the entire headline orange/red.

Editable renderer tokens live in [../assets/style.json](../assets/style.json). Keep those tokens and this guide aligned when changing the shared palette. The warm-neutral palette is the current proposal in response to the feedback; the headline-first layout and compact orange/red brand have been selected.

## Composition

- Use headline-first: small brand label, then the main headline, then the supporting photo or topic visual. The words carry the idea; the artwork supports it.
- Portrait default: 1080×1920. Keep essential content within the central x=90–990, y=420–1500 region as a starting design aid. Inspect the full image, central square and 3:4 crop.
- Landscape default: 1920×1080. Keep roughly 90px outer margins. Put the headline on the left and the supporting visual on the right, with clear separation and a quiet lower-right corner.
- Use comfortable whitespace, clear alignment and 2–3 short headline lines where possible. Prefer deliberate line breaks over tiny type.
- Ask for a separate creator photo or make a cover without their face, following `../SKILL.md`. Taking a portrait from the video remains an explicitly requested optional route.
- For a cover without the creator's face, use one meaningful topic visual or a strong typographic treatment. Do not reserve a blank portrait area or reuse a previous video's topic object.

## Restraint

Avoid neon cyan/purple as default palettes, luminous outlines, futuristic grids, glossy 3D objects, decorative italic lettering, heavy gradients and visual clutter. A subdued secondary colour or natural photo is welcome when it helps the actual topic. Do not force every subject into a beige map template; retain the editorial principles while adapting the content.

Do not add handles, episode labels, performance claims or badges without project support. Use original tool logos when relevant and available, without unnecessary name cards.

## Improve without rewriting past covers

Keep the selected composition, style-token snapshot and source/licence records in each project. Increment the shared version when the design changes. Older images and their snapshots stay unchanged unless a refresh is requested. A layout/style choice never substitutes for video-frame/audio approval.
