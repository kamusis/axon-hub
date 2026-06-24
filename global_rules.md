# Coding guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Language rules
- When asked questions in a specific language, respond in the same language. All code-related output must remain in English.
- If explicitly requested to translate or generate text in non-English and the file is markdown, proceed. Any text inside code must still be English; this typically applies to source files (e.g., `.py`, `.ts`) rather than markdown.
- Always use English in source code, including:
  - Code comments and documentation
  - User interface messages
  - Error messages and warnings
  - Log messages
  - Debug information
  - Console output
  - Configuration files
  - API responses
  - Status messages
  - Prompts and confirmations

# Community platform language rules
- Always use English for any content posted to international community platforms, including:
  - GitHub: issues, pull requests, comments, reviews, commit messages, release notes
  - Reddit: posts and replies (any subreddit)
  - Any other English-speaking communities (Hacker News, Discord public servers, Stack Overflow, etc.)

# Code quality
- Always include docstrings for functions and classes.
- Add meaningful comments for complex logic.
- Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.

# Git hygiene
- When asked to initializing a repo (`git init`), always create a `.gitignore` at the same time.
- Always add standard recommended items to `.gitignore` based on the project's programming language.
- When performing a `git init` operation, the default branch name must always be configured or created as `main`, not `master`.

# MoClaw CLI
- When using the `moclaw` CLI inside a git repository, first look for a moclaw workspace with the same name as the git repository and use that workspace. If not found, look for the project in current workspace with the same name as the git repository, if still not found, STOP and raise the error.

# Communication style
- Maintain professional objectivity, technical accuracy, and truthfulness.
- Avoid overly exaggerated expressions, flattery, or colloquial conversational filler.
- All technical and status updates must be rigorous, clear, concise, and restrained.
