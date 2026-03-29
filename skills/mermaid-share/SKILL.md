---
name: mermaid-share
description: Render Mermaid code to an SVG, JPG, or PNG and upload it to S.EE to return shareable links. Use this whenever the user gives Mermaid diagram code and wants a hosted image URL, image link, Markdown embed, or asks to render then upload/share a diagram in one flow.
version: 1.2.0
user-invocable: true
metadata:
  openclaw:
    emoji: "🧩"
    requires: { "bins": ["node", "uv", "python3"], "env": ["SEE_API_TOKEN"] }
    primaryEnv: "SEE_API_TOKEN"
---

# Mermaid Share

Turn Mermaid code into a hosted image by orchestrating the sibling `mermaid-viz` and `see-uploader` skills. Supports SVG, JPG, and PNG formats.

## When to use

Use this skill when the user:

- provides Mermaid code and wants a hosted link
- wants a Mermaid diagram rendered and then uploaded in one step
- asks for Markdown, HTML, or direct links for a Mermaid diagram
- wants to compare themes and publish one of the rendered images

## Prerequisites

- `node`
- `uv`
- `python3`
- `SEE_API_TOKEN`
- sibling skill directories `../mermaid-viz` and `../see-uploader`

## Workflow

1. Read the Mermaid code from the user request.
2. Choose a theme and output format (SVG, JPG, or PNG). Default to `zinc-dark` and `SVG` unless specified.
3. Check whether the current environment already satisfies the dependencies of `mermaid-viz` and `see-uploader`. Do not install anything unless a required dependency is actually missing.
4. Use the sibling `mermaid-viz` skill to validate the Mermaid header and confirm that the diagram type is supported before rendering.
5. If `mermaid-viz` reports that the diagram type is unsupported, stop immediately and tell the user. Do not continue to rendering output handling or upload.
6. If the type is supported, use the sibling `mermaid-viz` skill to render the Mermaid code to the requested file format (SVG, JPG, or PNG).
7. Use the sibling `see-uploader` skill to upload that file to S.EE.
8. Return the upload result, including direct link and Markdown embed.

## Usage

### Agent workflow

When this skill triggers:

- invoke `mermaid-viz` to validate the Mermaid type first
- stop immediately if `mermaid-viz` reports that the type is unsupported
- invoke `mermaid-viz` to produce the image (SVG, JPG, or PNG) only after the type check passes
- pass the generated file path to `see-uploader`
- return the upload output to the user

## Output

Return:

- local image file path
- upload status
- direct link
- Markdown embed
- HTML embed

## Supported Themes

`zinc-light`, `zinc-dark`, `tokyo-night`, `tokyo-night-storm`, `tokyo-night-light`, `catppuccin-mocha`, `catppuccin-latte`, `nord`, `nord-light`, `dracula`, `github-light`, `github-dark`, `solarized-light`, `solarized-dark`, `one-dark`.

## Rules

- Check the environment before installing anything.
- Reuse the sibling skills directly; do not add a separate renderer or uploader implementation here.
- Rely on `mermaid-viz` for the initial Mermaid type validation before any rendering or upload step.
- Fail fast with the underlying tool output if rendering or upload fails.
- If the diagram type is unsupported, stop before generating files or uploading anything.
- Treat this as a two-step orchestration skill, not a standalone tool implementation.
- Preserve actual newlines in Mermaid input.
- Support SVG, JPG, and PNG output as provided by the underlying `mermaid-viz` skill.
