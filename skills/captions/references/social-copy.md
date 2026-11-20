# Social posting copy

Use this reference when creating or revising social copy, including a cover-and-caption request for an existing project. Read the approved script and project context first.

## Default platform package

Unless the creator asks for a different set, provide all four platforms in one posting-copy file:

- **Instagram:** a fast visual hook, strictly concise context proportional to video length (1-2 sentences for short clips, no padded essays), a clear invitation to respond or follow, and relevant hashtags.
- **YouTube:** a separate title and description. Use the heading YouTube Shorts for a portrait reel and YouTube for a landscape video. Put the call to action and hashtags in the description.
- **TikTok:** shorter, direct copy that fits the same video, with a relevant question or invitation and hashtags.
- **LinkedIn:** a standalone professional post in the creator's voice structured for high scannability. Bold the opening hook, bold the lead-in phrase of every bullet point, bold key thesis phrases, and bold platform labels in the follow block (**YouTube:**, **Instagram:**, **TikTok:**). Invite a relevant conversation and use a few relevant hashtags when they fit.

For LinkedIn, develop a specific story from the actual project or creator experience rather than expanding the reel caption with generic filler. A concrete opening, a relevant detail from the work, and a natural invitation to other professionals should make it useful on its own. For creator/channel introductions, include a concise where-to-follow block with the creator's known YouTube, Instagram and TikTok links. Use direct project/video URLs when supplied; otherwise clearly label profile links. Reuse saved project links or the creator's verified channel references, ask for missing destinations, and never infer a URL from a shared handle. Save supplied links with the local project for later reuse.

Adapt each post to its audience. Do not paste the same paragraph into every section. Reuse the saved creator name and handle. Keep internal edit-version labels out of posting copy unless the video is about that edit.

## Writing preference

Write like the creator talking to another person: specific, plain language, natural contractions and varied sentence lengths. Ground claims in the script and saved project facts.

Never use an em dash (Unicode U+2014) in authored posting copy, including titles. Rewrite the sentence with a full stop, comma or natural phrasing instead.

Avoid stock AI-style phrasing, inflated claims, forced punchlines, repetitive sentence patterns and generic engagement bait. Do not use canned openings such as "In today's fast-paced world", "unlock the power", "game changer" or "This isn't about X. It's about Y." Keep enthusiasm proportional to what the creator actually says. Do not invent results, metrics, links or promises.

### Strict Brevity (No Walls of Text)
Most viewers and readers scroll quickly and will skip large walls of text. Keep all platform copy concise, high-signal, and easy to skim. Deliver the core value and primary takeaway upfront. For LinkedIn, keep total post length compact (under 150 words) with short 1-2 sentence paragraphs and concise bullets rather than long essays. For Instagram, keep context to 1-2 sentences.

### Search Engine Optimization (SEO)
Structure copy for discovery across YouTube search, Google, LinkedIn search, Instagram Explore, and TikTok search:
- Front-load high-intent search keywords (e.g. mobile app development, iOS/Android, AI workflows, coding tools) in titles and the first 1-2 lines before the platform's "more" fold.
- Match titles to actual search queries developers and learners look for.
- Use a targeted mix of broad and specific technical hashtags for categorization and search reach.

This preference governs newly authored social copy. Preserve approved spoken scripts and historical caption files unless the user asks to revise them. The dashboard preserves the words; its presentation and clipboard behavior interpret only the supported authoring markers described below.

## Platform formatting

Format generated posts for their destination. Use emphasis sparingly when it helps someone scan the post. Avoid decorative Unicode font substitutions, forced all-caps headings and raw Markdown pasted into a plain caption.

For LinkedIn posts and YouTube descriptions, build a readable, highly scannable hierarchy. For LinkedIn, always use real bullet characters (`•`) and bold the lead-in phrase of each bullet point (e.g. `• **Key takeaway:** ...`), bold the platform labels beside social URLs (`**YouTube:** <url>`, `**Instagram:** <url>`, `**TikTok:** <url>`), and bold key thesis phrases or contrasts. Never use raw asterisks (`*`) or hyphens (`-`) for list items. Use italic for a role such as "software developer" or a short supporting phrase. Separate ideas into short paragraphs; concise, bold-headed bullets make technical insights easy to scan. Leave URLs in normal text, and keep each styled phrase on a single line without nesting styles.

Keep social profile links compact: one labeled URL per line with bold platform labels, without blank lines between platforms.

| Destination | Authoring and copying |
| --- | --- |
| Instagram caption | Normal text with short paragraphs, blank lines and simple bullet characters if needed. Keep concise and proportional to clip length. Do not add bold/italic Markdown or decorative fonts. |
| YouTube title | Normal text. Do not add formatting markers. |
| YouTube description | May use bold, italic and strikethrough. In the saved source use `**bold**`, `*italic*` and `~~strikethrough~~` on a single line, without nesting. Use bullet characters (`•`) for lists. The dashboard previews these styles and Copy formatted supplies rich text with a matching plain-text fallback. |
| TikTok video caption | Normal text with spacing, hashtags and mentions. Text overlays and text-post design tools are separate from a video's caption. |
| LinkedIn feed post | Use bold emphasis for scannability: bold opening hook, real bullet point characters with bold lead-ins (`• **Heading:** ...`), bold platform labels in follow links, and bold key thesis phrases. Never use raw asterisks (`*`). The dashboard previews the same inline markers and offers Copy formatted. Check which styles your LinkedIn post composer retains. |

The dashboard removes the supported authoring markers from normal-text copies while preserving the words, paragraphs, bullets, hashtags and mentions. Source HTML is treated as literal text. If a browser cannot copy rich text, it copies normal text and reports that fallback. Pasting rich text does not guarantee that the destination will retain it: check YouTube Studio or the LinkedIn post composer after pasting and use its native formatting controls where available.

Formatting references checked 2026-11-16:

- [YouTube description formatting](https://support.google.com/youtube/answer/12948449) documents bold, italic, strikethrough and lists.
- [Instagram publishing caption field](https://developers.facebook.com/documentation/instagram-platform/content-publishing) and [TikTok video caption field](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post) document their caption-text surfaces. Treat these captions as normal text in this workflow.
- A [first-hand report on LinkedIn native bold](https://www.linkedin.com/pulse/linkedin-posts-now-have-native-bold-text-so-what-lynnaire-johnston-mg3ue), published October 1, 2026, describes formatted pasting into feed posts for some accounts. Enable formatted copying for LinkedIn and verify the destination composer. The [Posts API text schema](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/little-text-format?view=li-lms-2026-09) does not establish the formatting capabilities of the interactive post editor.

Recheck the relevant official guidance before promising newly added formatting support.

## File format and delivery

For YouTube descriptions and LinkedIn posts, the saved source can use `**bold**`, `*italic*` and `~~strikethrough~~` when emphasis helps and the destination supports it. These are simple inline markers: keep each marked phrase on one line and do not nest styles. Use emphasis sparingly, such as a short opening phrase, rather than styling whole paragraphs. The dashboard previews these styles and copies rich HTML plus matching normal text. The destination may strip pasted formatting, so check YouTube Studio or the LinkedIn post composer and use the available native controls when needed.

Use normal text for Instagram captions, TikTok video captions and YouTube titles in this workflow. Short paragraphs, blank lines and ordinary bullet characters provide structure without pretending that Markdown or HTML will style those fields. Do not substitute decorative Unicode letters for bold or italic by default. LinkedIn articles and TikTok text overlays are different publishing surfaces and are not the feed/video copy requested here.

Update the project's existing posting-copy file. If none exists, create `publishing/Social_Copy.md`. Avoid multiple active caption files with competing versions.

Use these headings so the dashboard can split the file into copyable sections:

```markdown
# Posting copy

## Instagram

[Instagram caption and hashtags]

## YouTube Shorts

Title: [YouTube title]

Description:
[YouTube description, call to action and hashtags]

## TikTok

[TikTok caption and hashtags]

## LinkedIn

[LinkedIn post and relevant hashtags]
```

Before delivery, check that all four platforms and the YouTube title/description exist, the new copy contains no em dashes, and each post matches the actual video. Verify the dashboard discovers the file and offers each section separately. Caption fields start closed. On desktop, show Instagram and TikTok side by side, YouTube title and description on the next row, and LinkedIn full width last. Stack the pairs on narrow screens. Click a label to expand the text and its Copy button.

Creating copy does not authorize publishing a social post.
