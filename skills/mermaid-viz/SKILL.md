---
name: mermaid-viz
description: Render Mermaid diagrams as beautiful ASCII/Unicode art for terminal display or SVG files for sharing. Use when the user asks to visualize logic, flows, state machines, or architecture.
version: 1.0.1
user-invocable: true
---

# Mermaid Visualization

Visualize complex logic and system architecture directly in the chat or as SVG files using `beautiful-mermaid`.

## Prerequisites

- Node.js
- `beautiful-mermaid`

## Installation

Check the current environment before installing anything. Reuse existing dependencies when available. Do not run installation commands by default.

Only install in this skill directory after confirming that `beautiful-mermaid` is missing from the current environment:

```bash
pnpm install
```

## Usage

You can generate two types of output:
1. **ASCII/Unicode** (Default): Best for immediate display in the chat.
2. **SVG**: Best for high-quality sharing or documentation.

### Rendering ASCII/Unicode (Immediate Display)

To show a diagram in the chat, use:
```bash
node scripts/mermaid-viz.js "diagram_code"
```

### Rendering SVG (File Output)

To save a high-quality SVG (remember to save to the `artifacts/` directory):
```bash
node scripts/mermaid-viz.js --type svg --theme tokyo-night --output artifacts/output.svg "diagram_code"
```

SVG background behavior:
- Transparent by default
- Pass `--opaque` to preserve the selected theme background color in the output SVG

To save an opaque SVG with the theme background:
```bash
node scripts/mermaid-viz.js --type svg --theme tokyo-night --opaque --output artifacts/output.svg "diagram_code"
```

## Available Themes (SVG only)
`zinc-light`, `zinc-dark`, `tokyo-night`, `tokyo-night-storm`, `tokyo-night-light`, `catppuccin-mocha`, `catppuccin-latte`, `nord`, `nord-light`, `dracula`, `github-light`, `github-dark`, `solarized-light`, `solarized-dark`, `one-dark`.

## Examples

### 1. Show a flowchart in chat
```bash
node scripts/mermaid-viz.js "flowchart LR
  A[User] --> B{Auth}
  B -->|Success| C[Dashboard]
  B -->|Fail| D[Login]"
```

### 2. Generate a sequence diagram SVG
```bash
node scripts/mermaid-viz.js --type svg --output artifacts/sequence.svg "sequenceDiagram
  Alice->>Bob: Hello Bob!
  Bob-->>Alice: Hi Alice!"
```

### 3. Generate an opaque SVG that preserves the theme background
```bash
node scripts/mermaid-viz.js --type svg --theme tokyo-night --opaque --output artifacts/sequence-opaque.svg "sequenceDiagram
  Alice->>Bob: Hello Bob!
  Bob-->>Alice: Hi Alice!"
```

## Supported Diagram Types
- `flowchart` (or `graph`)
- `sequenceDiagram`
- `stateDiagram-v2`
- `classDiagram`
- `erDiagram`

## Rules
- **Type check first**: Inspect the first Mermaid header line before rendering. If the diagram type is not one of the supported types above, stop immediately and tell the user that this skill cannot render it with `beautiful-mermaid`.
- **Formatting**: Always ensure the first line of the diagram code contains the type (e.g., `flowchart TD`).
- **Early failure**: If the type check fails, do not attempt rendering, file generation, or any follow-up workflow.
- **Background choice**: SVG output is transparent by default. Use `--opaque` only when the user explicitly wants a solid background or when the rendered SVG should preserve the selected theme as a standalone image.
- **Embedding preference**: Prefer transparent SVG output for blog posts, documentation pages, and mixed light/dark layouts unless the user asks to keep the theme background.
- **Newlines**: Use actual newlines in the diagram code string.
- **Escape**: Be careful with special characters in the shell.
