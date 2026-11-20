---
name: captions
description: Author and revise multi-platform social captions and posting copy (Instagram, YouTube title/description, TikTok, LinkedIn) for any video project or topic using the Techno Ravan style standard, with zero em dashes, platform-optimized formatting, and dashboard integration.
---

# Social Captions & Posting Copy

Resolve the studio root two directories above this skill. Use this skill when authoring or revising social copy for a video project or draft, or when triggered by `/captions` or `/social-copy`.

Read [references/social-copy.md](references/social-copy.md) before writing copy.

---

## 1. Understand the Project Context

1. **Read the Source Project**:
   - Check the project's approved script (`plan.json`, `review.html`, or `intro-reel-script.md`).
   - Read the video metadata, export details, topic brief, and any verified facts or timestamps.
   - If the request targets a specific project slug (e.g. in `outputs/reels/` or `outputs/videos/`), inspect its existing `publishing/Social_Copy.md` or `export/caption.txt` if present.
2. **Identify the Core Message**:
   - Ground claims strictly in what the creator actually says and builds.
   - Do not invent metrics, unverified features, or inflated promises.
   - Write in Techno Ravan's authentic creator voice: clear, practical, direct, and enthusiastic without corporate jargon.

---

## 2. Writing Rules & Core Constraints

### A. Zero Fluff, Maximum Brevity (No Walls of Text)
- **Respect the Reader's Time**: Most people scroll fast and skip long walls of text. Keep copy across **ALL** platforms short, punchy, and high-signal. Never write bloated essays or multi-paragraph filler.
- **Front-Load the Value**: Deliver the core takeaway immediately in the first sentence.
- **High Scannability**: Use short 1-2 sentence paragraphs, clean whitespace, and bold lead-in tags on all bullet points.
- **Real Bullet Points (`•`)**: Always use the actual bullet point symbol (`•`, Unicode `U+2022`) for all lists instead of raw asterisks (`*`) or hyphens (`-`). Raw asterisks look like unrendered markdown or code symbols (`*`) in feeds. Always format bullets as: `• **Key Topic:** description`.
- **Zero Em Dashes**: Never use an em dash (`—`, Unicode `U+2014`) anywhere in newly authored posting copy, including titles. Rewrite the sentence with a full stop, comma, colon, or natural phrasing.
- **No Canned AI Openings**: Avoid cliché openings like *"In today's fast-paced world"*, *"Unlock the power of"*, *"Game changer"*, or *"This isn't about X. It's about Y."*
- **Distinct Platform Voices**: Tailor each post to how that audience consumes content while keeping every format concise.

### B. SEO & Organic Discovery (Search-Optimized Copy)
Every caption must be engineered to rank in platform search (YouTube Search, LinkedIn Search, Google, Instagram Explore, TikTok Search):
- **Front-Load Search Keywords**: Place high-intent search terms (e.g. *Mobile App Development, AI Engineering, Coding Agents, iOS/Android Architecture*) in the title and the first 1-2 lines before the "see more" cutoff.
- **Searchable Titles**: Craft punchy titles that mirror actual user search queries (under 65 characters) with clear intent.
- **Semantic Keyword Integration**: Naturally weave relevant technical keywords into bullet points and takeaways so search indexers categorize the content correctly.
- **High-Intent Hashtags**: Combine broad category tags (e.g. `#SoftwareEngineering`, `#Coding`) with specific search tags that developers and tech audiences search for (e.g. `#MobileDevelopment`, `#AIWorkflows`).

---

## 3. Platform Breakdown

### A. Instagram
- **Goal**: Fast visual hook, direct to-the-point context, natural engagement prompt, and targeted hashtags.
- **Brevity & SEO Rule**: Strictly concise (under 50 words). No walls of text or padded essays. Include 1 primary search keyword in the first sentence, 1 engaging question, and 4-6 targeted SEO hashtags.
- **Formatting**: Normal text with short 1-2 sentence paragraphs and clean blank lines.
- **Do NOT use**: Bold/italic Markdown or decorative Unicode fonts.

### B. YouTube / YouTube Shorts
- **Heading**: Use `## YouTube Shorts` for vertical (9:16) portrait reels, or `## YouTube` for horizontal (16:9) landscape videos.
- **Title**: Punchy, highly searchable, concise title (under 65 characters recommended). Include primary search keywords front-loaded. Plain text only.
- **Description**:
  - First 2 lines: Search-optimized summary featuring core keywords (visible before "Show more").
  - 2-3 concise bullet points using `•` with bold lead-in tags (`• **Key Topic:** 1-line detail`).
  - Clear, brief call to action (subscribe / check links).
  - 4-6 relevant SEO hashtags (e.g. `#SoftwareEngineering #MobileDevelopment #Coding #AI`).
  - **Formatting**: YouTube descriptions support inline `**bold**`, `*italic*`, and `~~strikethrough~~`. Keep each styled phrase on a single line (no nesting).
  - **Length**: Compact and scannable (under 100 words total).

### C. TikTok
- **Goal**: Short, immediate, punchy caption optimized for TikTok search.
- **Structure**: 1-2 punchy sentences containing primary search keywords + 4-6 high-relevance hashtags. Normal text only.

### D. LinkedIn
- **Goal**: Professional developer story engineered for fast reading and search discovery without walls of text (under 150 words total).
- **Scannability & Bolding Rules (Mandatory)**:
  - **Real Bullet Points with Bold Headings**: Every bullet point MUST use the bullet symbol (`•`) followed by a bold lead-in phrase or core takeaway (e.g. `• **Orchestration over boilerplate:** Moving from manual setup...`). Never use asterisks (`*`) or plain, unstyled bullets.
  - **Bold Social Platform Labels**: In the follow block, ALWAYS bold the platform labels (`**YouTube:** <url>`, `**Instagram:** <url>`, `**TikTok:** <url>`). Keep them on single lines without blank lines between them.
  - **Bold Key Insights**: Bold the opening hook and key thesis phrases (e.g. `**accelerating the iteration cycle**`, `**knowing how to frame problems**`) so busy professionals skimming the feed immediately grasp the core message.
  - Keep each bold phrase on a single line (no nesting).
- **Structure**:
  1. Concrete opening line (bolded, front-loaded with primary SEO keywords).
  2. 1-2 concise setup sentences framing the engineering lesson or shift.
  3. 2-3 tight bulleted takeaways using `•` with bold lead-ins on every bullet.
  4. 1 concise takeaway sentence highlighting engineering judgment or trade-offs.
  5. A natural 1-line question inviting developer discussion.
  6. Compact social profile links block with bold platform labels:
     ```markdown
     Follow along:
     **YouTube:** https://youtube.com/@TechnoRavan
     **Instagram:** https://instagram.com/technoravan
     **TikTok:** https://tiktok.com/@technoravan
     ```
  7. 4-6 professional SEO hashtags (e.g. `#SoftwareEngineering #MobileDevelopment #AI #TechCareers`).

---

## 4. Delivery File Format

Always deliver the output in the standard multi-platform markdown structure so the local dashboard ([`dashboard/captions.mjs`](../../dashboard/captions.mjs)) automatically discovers it and provides one-click copy buttons for each platform.

Save to: `<project_dir>/publishing/Social_Copy.md`

```markdown
# Posting copy

## Instagram

[Instagram caption and hashtags]

## YouTube Shorts

Title: [YouTube Title]

Description:
[YouTube description, call to action, and hashtags]

## TikTok

[TikTok caption and hashtags]

## LinkedIn

[LinkedIn post and relevant hashtags]
```

*(For landscape videos, replace `## YouTube Shorts` with `## YouTube`).*

---

## 5. Verification Checklist

Before reporting completion:
1. Ensure all four platforms (Instagram, YouTube Title/Description, TikTok, LinkedIn) are present.
2. Verify **zero em dashes (`—`)** exist anywhere in the text.
3. Verify **brevity across all platforms**: No walls of text; keep each post tight, punchy, and quick to read.
4. Verify **SEO optimization**: Primary search keywords are front-loaded in titles, opening lines, and hashtags for discovery.
5. Verify **LinkedIn formatting**:
   - Every bullet point uses a real bullet character (`•`) with a bold lead-in (`• **Core Point:** ...`); never use raw asterisks (`*`) or hyphens (`-`).
   - All social links in the follow block have bold platform labels (`**YouTube:**`, `**Instagram:**`, `**TikTok:**`).
   - Key thesis phrases are bolded.
6. Confirm social links use verified creator references and are formatted compactly without blank lines between them.
7. Verify the file is saved at `publishing/Social_Copy.md` so the review dashboard immediately detects it.
8. Present the drafted copy in your reply with quick-read formatting.
