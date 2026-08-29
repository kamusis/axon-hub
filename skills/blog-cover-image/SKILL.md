---
name: blog-cover-image
description: >
  Generate a unique 1K cover image for a blog post via 'nano-banana-pro' based on the article
  title. Whimsical storybook illustration style: hand-drawn feel, rich textures, soft warm
  lighting, intricate backgrounds. Blends technical themes with imaginative, cozy elements
  (e.g., animals using vintage tech). Aims for a 'vintage wonder' aesthetic. Avoids generic
  neon sci-fi.
  Use when asked to generate a blog/WeChat/公众号 article cover (题图/封面/cover/header image).
  Source rule: scripts/hn_patrol.sh (Hacker News Patrol).
---

# Blog Cover Image

Produce one unique cover image per blog article, upload it via S.EE, and automatically embed it into the target article.

## Tool & Specifications

- **Engine / Tool**: `generate_image` / `nano-banana-pro`
- **Aspect Ratio**: `16:9` (or `3:2` / `1K` resolution)
- **Trigger basis**: Article title and core theme
- **Uploader**: `see-uploader` (`C:\Users\kamus\.gemini\config\skills\see-uploader\scripts\upload.py`)

## Style Spec

- Illustration type: whimsical, highly detailed **storybook illustration**
- Hand-drawn feel
- Rich textures
- Soft warm lighting
- Intricate backgrounds
- Aesthetic target: **vintage wonder**
- Theme blend: technical subject + imaginative/cozy elements
  - Example: small whimsical creatures/animals operating vintage computing terminals, glowing conduits, clockwork modules, or mechanical consoles
- **Avoid**: generic neon sci-fi, bland stock 3D renders

## End-to-End Workflow

1. **Analyze Title & Subject**:
   - Extract the article title and core technical theme as the visual seed.
2. **Craft Prompt**:
   - Encode the style spec (storybook illustration, hand-drawn feel, warm lighting, cozy vintage wonder) + the subject's metaphor.
3. **Generate Image**:
   - Call `generate_image` with `AspectRatio: "16:9"` and a concise `ImageName` (e.g. `runtime_deep_dive_cover`).
4. **Upload via S.EE**:
   - Run the upload script from `see-uploader`:
     ```bash
     python C:\Users\kamus\.gemini\config\skills\see-uploader\scripts\upload.py --file <path_to_generated_image>
     ```
   - Extract the direct URL (`https://files.seeusercontent.com/...`).
5. **Update the Target Article**:
   - Locate the cover position in the article markdown: directly under the main H1 `# Title` (or lead blockquote), before the first `---` divider or Section 1.
   - Insert the cover image markdown tag:
     ```markdown
     ![<Article Title>](https://files.seeusercontent.com/...)
     ```
6. **Report**:
   - Report the generated image prompt, direct S.EE URL, and confirmation of article update.

## Prompt Skeleton

```
A whimsical, highly detailed storybook illustration for an article titled "<TITLE>".
Hand-drawn feel, rich textures, soft warm lighting, intricate background.
Vintage wonder aesthetic. Blend the technical theme with imaginative, cozy elements
(e.g., small animals or charming clockwork robots interacting with vintage tech consoles and glowing conduits). Avoid generic neon sci-fi. 16:9 aspect ratio.
```

## Rules

- One cover per article — never reuse across posts.
- Style stays consistent across the series; only the subject and metaphor swap.
- If the subject resists cozy framing (e.g., outage, security breach), soften with metaphor — keep style, drop shock value.
- Always complete the upload to S.EE and insert the URL directly into the target markdown file.