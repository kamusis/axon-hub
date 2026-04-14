---
name: mermaid-viz
description: Render Mermaid diagrams as beautiful ASCII/Unicode art for terminal display, or SVG/JPG/PNG files for sharing. Use when the user asks to visualize logic, flows, state machines, or architecture.
version: 1.2.0
user-invocable: true
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["node", "bash"]
      npm: ["beautiful-mermaid", "sharp"]
    exec:
      # mermaid-viz wrapper script handles path resolution internally
      wrapper: "./mermaid-viz"
---

# Mermaid Visualization

Visualize complex logic and system architecture directly in the chat, or as SVG/JPG/PNG files using `beautiful-mermaid` and `sharp`.

## Prerequisites

- Node.js
- `beautiful-mermaid`
- `sharp`

## Installation

Check the current environment before installing anything. Reuse existing dependencies when available. Do not run installation commands by default.

Only install in this skill directory after confirming that `beautiful-mermaid` is missing from the current environment:

```bash
pnpm install
```

**CRITICAL Prerequisites for File Output:**
1. **Create output directory first** — Before rendering to a file, ensure the output directory exists (e.g., `/tmp/` always exists, or create `artifacts/` if needed).
2. **Use simple single commands** — OpenClaw exec security policy rejects commands with `&&`, `||`, pipes `|`, or redirects `2>&1`. Use only direct `node <script> <args>` format.

## Usage

You can generate four types of output:
1. **ASCII/Unicode** (Default): Best for immediate display in the chat.
2. **SVG**: Best for high-quality sharing or documentation.
3. **JPG**: Best for quick viewing on platforms with limited SVG support.
4. **PNG**: Lossless bitmapped image format with transparency support.

### Rendering ASCII/Unicode (Immediate Display)

To show a diagram in the chat, use:
```bash
./mermaid-viz "diagram_code"
```

Or call the Node script directly (must be run from skill directory):
```bash
node scripts/mermaid-viz.js "diagram_code"
```

### Rendering SVG/JPG/PNG (File Output)

**CRITICAL**: 
- **Output directory must exist** — Create it first if using `artifacts/`, or use `/tmp/` which always exists.
- **No shell operators** — Do NOT use `&&`, `||`, `|`, or `2>&1`. Use the `./mermaid-viz` wrapper script (recommended) or simple `node scripts/mermaid-viz.js ...` only.

To save a high-quality file (examples use `/tmp/` which requires no setup):
```bash
./mermaid-viz --type svg --theme tokyo-night --output /tmp/output.svg "diagram_code"
./mermaid-viz --type jpg --theme tokyo-night --output /tmp/output.jpg "diagram_code"
./mermaid-viz --type png --theme tokyo-night --output /tmp/output.png "diagram_code"
```

If you must use `artifacts/` directory, create it in a **separate exec call** first:
```bash
mkdir -p artifacts
```
Then run the render command.

Background behavior:
- **SVG**: Transparent by default. Pass `--opaque` to preserve the theme background.
- **JPG**: Always uses the theme background (or a default dark color).
- **PNG**: Transparent by default. Pass `--opaque` to flatten with the theme background.

### Available Themes (SVG/JPG only)
`zinc-light`, `zinc-dark`, `tokyo-night`, `tokyo-night-storm`, `tokyo-night-light`, `catppuccin-mocha`, `catppuccin-latte`, `nord`, `nord-light`, `dracula`, `github-light`, `github-dark`, `solarized-light`, `solarized-dark`, `one-dark`.

## Examples

### 1. Show a flowchart in chat
```bash
./mermaid-viz "flowchart LR
  A[User] --> B{Auth}
  B -->|Success| C[Dashboard]
  B -->|Fail| D[Login]"
```

### 2. Generate a sequence diagram JPG
```bash
./mermaid-viz --type jpg --output /tmp/sequence.jpg "sequenceDiagram
  Alice->>Bob: Hello Bob!
  Bob-->>Alice: Hi Alice!"
```

### 3. Generate an opaque SVG
```bash
./mermaid-viz --type svg --theme tokyo-night --opaque --output /tmp/sequence-opaque.svg "sequenceDiagram
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
- **Security policy compliance**: All exec commands must be simple single commands. No `&&`, `||`, pipes `|`, redirects `2>&1`, or subshells `$(...)`. Create directories in separate calls before file operations. **Use the `./mermaid-viz` wrapper script** to avoid path resolution issues — it handles locating the script internally.
- **Type check first**: Inspect the first Mermaid header line before rendering. If the diagram type is not one of the supported types above, stop immediately and tell the user that this skill cannot render it with `beautiful-mermaid`.
- **Formatting**: Always ensure the first line of the diagram code contains the type (e.g., `flowchart TD`).
- **Early failure**: If the type check fails, do not attempt rendering, file generation, or any follow-up workflow.
- **Background choice**: SVG output is transparent by default. Use `--opaque` only when the user explicitly wants a solid background or when the rendered SVG should preserve the selected theme as a standalone image.
- **Embedding preference**: Prefer transparent SVG output for blog posts, documentation pages, and mixed light/dark layouts unless the user asks to keep the theme background.
- **Newlines**: Use actual newlines in the diagram code string.
- **Escape**: Be careful with special characters in the shell.
