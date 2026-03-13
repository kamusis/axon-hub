---
name: mermaid-viz
description: Render Mermaid diagrams as beautiful ASCII/Unicode art for terminal display or SVG files for sharing. Use when the user asks to visualize logic, flows, state machines, or architecture.
version: 1.0.0
user-invocable: true
---

# Mermaid Visualization

Visualize complex logic and system architecture directly in the chat or as SVG files using `beautiful-mermaid`.

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

## Supported Diagram Types
- `flowchart` (or `graph`)
- `sequenceDiagram`
- `stateDiagram-v2`
- `classDiagram`
- `erDiagram`

## Rules
- **Formatting**: Always ensure the first line of the diagram code contains the type (e.g., `flowchart TD`).
- **Newlines**: Use actual newlines in the diagram code string.
- **Escape**: Be careful with special characters in the shell.
