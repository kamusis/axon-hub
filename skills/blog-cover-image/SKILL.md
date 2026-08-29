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

Produce one unique cover image per blog article.

## Tool

- **Engine**: `nano-banana-pro`
- **Resolution**: 1K
- **Trigger basis**: article title (each article → unique image)
- **Execution**: local VPS only (no remote generation)

## Style Spec

- Illustration type: whimsical, highly detailed **storybook illustration**
- Hand-drawn feel
- Rich textures
- Soft warm lighting
- Intricate backgrounds
- Aesthetic target: **vintage wonder**
- Theme blend: technical subject + imaginative/cozy elements
  - Example: animals using vintage tech
- **Avoid**: generic neon sci-fi

## Workflow

1. Take the article title as the visual seed.
2. Craft a prompt that encodes the style spec above + the title's core subject.
3. Call `nano-banana-pro` locally. Request 1K output.
4. Save the image to the post's asset directory (next to the article markdown).
5. Reference the image path in the renderer (e.g., `wechat_master_renderer.py` `thumb_media_id` upload).

## Prompt Skeleton

```
A whimsical, highly detailed storybook illustration for an article titled "<TITLE>".
Hand-drawn feel, rich textures, soft warm lighting, intricate background.
Vintage wonder aesthetic. Blend the technical theme with imaginative, cozy elements
(e.g., animals using vintage tech). Avoid generic neon sci-fi. 1K resolution.
```

## Rules

- One cover per article — never reuse across posts.
- Style stays consistent across the series; only the subject swaps.
- If the subject resists cozy framing (e.g., outage, security breach), soften with metaphor — keep style, drop shock value.