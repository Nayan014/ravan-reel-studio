# Social posting copy

Use this reference when creating or revising social copy, including a cover-and-caption request for an existing project. Read the approved script and project context first.

## Default platform package

Unless the creator asks for a different set, provide all four platforms in one posting-copy file:

- **Instagram:** a relevant opening, enough context for the reel, a clear invitation to respond or follow, and relevant hashtags.
- **YouTube:** a separate title and description. Use the heading YouTube Shorts for a portrait reel and YouTube for a landscape video. Put the call to action and hashtags in the description.
- **TikTok:** shorter, direct copy that fits the same video, with a relevant question or invitation and hashtags.
- **LinkedIn:** a standalone professional post in the creator's voice. Explain the actual project, experience or lesson, and invite a relevant conversation. Use a few relevant hashtags when they fit.

For LinkedIn, develop a specific story from the actual project or creator experience rather than expanding the reel caption with generic filler. A concrete opening, a relevant detail from the work, and a natural invitation to other professionals should make it useful on its own. For creator/channel introductions, include a concise where-to-follow block with the creator's known YouTube, Instagram and TikTok links. Use direct project/video URLs when supplied; otherwise clearly label profile links. Reuse saved project links or the creator's verified channel references, ask for missing destinations, and never infer a URL from a shared handle. Save supplied links with the local project for later reuse.

Adapt each post to its audience. Do not paste the same paragraph into every section. Reuse the saved creator name and handle. Keep internal edit-version labels out of posting copy unless the video is about that edit.

## Writing preference

Write like the creator talking to another person: specific, plain language, natural contractions and varied sentence lengths. Ground claims in the script and saved project facts.

Never use an em dash (Unicode U+2014) in authored posting copy, including titles. Rewrite the sentence with a full stop, comma or natural phrasing instead.

Avoid stock AI-style phrasing, inflated claims, forced punchlines, repetitive sentence patterns and generic engagement bait. Do not use canned openings such as "In today's fast-paced world", "unlock the power", "game changer" or "This isn't about X. It's about Y." Keep enthusiasm proportional to what the creator actually says. Do not invent results, metrics, links or promises.

This preference governs newly authored social copy. Preserve approved spoken scripts and historical caption files unless the user asks to revise them. The dashboard preserves the words; its presentation and clipboard behavior interpret only the supported authoring markers described below.

## Platform formatting

Format generated posts for their destination. Use emphasis sparingly when it helps someone scan the post. Avoid decorative Unicode font substitutions, forced all-caps headings and raw Markdown pasted into a plain caption.

| Destination | Authoring and copying |
| --- | --- |
| Instagram caption | Normal text with short paragraphs, blank lines and, when useful, simple bullet characters. Do not add bold/italic Markdown or decorative fonts. |
| YouTube title | Normal text. Do not add formatting markers. |
| YouTube description | May use bold, italic and strikethrough. In the saved source use `**bold**`, `*italic*` and `~~strikethrough~~` on a single line, without nesting. The dashboard previews these styles and Copy formatted supplies rich text with a matching plain-text fallback. |
| TikTok video caption | Normal text with spacing, hashtags and mentions. Text overlays and text-post design tools are separate from a video's caption. |
| LinkedIn feed post | Use light bold emphasis when useful, such as a short opening line. The dashboard previews the same inline markers and offers Copy formatted. Check which styles your LinkedIn post composer retains. Keep paragraphs and optional plain bullets readable. |

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
