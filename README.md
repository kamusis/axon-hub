# Axon Hub

The centralized repository for AI agent skills, workflows, and commands managed by [Axon CLI](https://github.com/kamusis/axon-cli).

---

## 📁 Structure

This repository follows the structure required by **Axon CLI** to synchronize context across different AI editors and tools:

- **`skills/`**: Markdown-based agent skills (following the [Agent Skills](https://agentskills.io) standard).
- **`workflows/`**: Reusable multi-step task chains (JSON/YAML).
- **`commands/`**: Custom executable scripts and command templates.

## 🚀 Usage

### Option 1: Consuming the Hub (Read-only)
If you want to use the public skills on your machine without managing your own repository:
```bash
axon init --upstream
axon link
```

### Option 2: Using as your own Source of Truth (Read-write)
If you want to manage your personal skills across multiple machines:
1. Create a private repository on GitHub.
2. Initialize Axon with your repository URL:
```bash
axon init git@github.com:your-user/your-axon-hub.git
axon link
```

### 🔄 Synchronizing
Keep all your local AI tools in sync with one command:
```bash
axon sync
```

## 🛠 Compatible Tools

Axon automatically bridges this Hub to the global configuration directories of:
- **Editors**: Cursor, Windsurf, Antigravity, PearAI, Neovate.
- **CLIs**: Claude Code, Codex, Gemini CLI, OpenCode.
- **Agents**: OpenClaw.

---

## License
MIT
