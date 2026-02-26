---
name: slidev
description: "Formalize the workflow for creating, refining, and deploying Slidev presentations from Markdown. Use when the user wants to: (1) Convert regular Markdown or text into a Slidev-compatible format, (2) Deploy a new slide presentation to the public VPS server, (3) Build static HTML from .md files using the workspace build script."
---

This skill automates the process of turning standard Markdown into a beautiful Slidev presentation hosted on your public VPS.

## Core Workflow

1.  **Input Acquisition**: Receive Markdown content directly as text or as a path to an existing file.
2.  **Intelligent Refinement**:
    -   **Frontmatter**: Ensure the Markdown starts with a Slidev configuration block. If missing, prepend a default block (see below).
    -   **Paging**: Scan for headers (`#`, `##`). If they aren't already preceded by `---` (Slidev's page divider), insert `---` before them to ensure proper slide separation.
3.  **Storage**: Save the refined Markdown into `/home/kamus/slidev-workspace/_posts/<normalized-name>.md`.
4.  **Building**: Execute the build script: `cd /home/kamus/slidev-workspace && ./build.sh [--theme <name>] <normalized-name>.md`.
5.  **Confirmation**: Provide the user with the public URL: `https://slides.kamusis.me/<normalized-name>/`.

## Guidelines for Refinement

-   **Normalization**: Always normalize the filename/URL slug (lowercase, replace spaces/special characters with hyphens, merge consecutive hyphens).
-   **Themes**: The `build.sh` script now supports a `--theme` flag. If specified, it will automatically update the `theme:` field in the Markdown frontmatter and apply the theme during build. Default is `shibainu`.
-   **Default Frontmatter**:
    ```yaml
    ---
    theme: seriph
    background: https://cover.sli.dev
    class: text-center
    highlighter: shiki
    drawings:
      persist: false
    transition: slide-left
    title: Welcome to Slidev
    ---
    ```
-   **Divider Placement**: Only insert the `---` divider if the line immediately preceding the header is not already `---` and is not part of the opening frontmatter block.

## Workspace Paths
-   **Workspace Root**: `/home/kamus/slidev-workspace`
-   **Posts Directory**: `_posts/`
-   **Build Script**: `./build.sh`
-   **Public URL Base**: `https://slides.kamusis.me/`
