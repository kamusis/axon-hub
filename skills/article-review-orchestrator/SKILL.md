---
name: article-review-orchestrator
description: Orchestrate article writing and review for finished drafts or article topics with reference links. Use this whenever the user wants a blog post, article, essay, technical writeup, or Markdown article to be reviewed, rewritten, polished, de-AI-fied, or turned into a publication-ready version. Also use it when the user provides only an article topic plus source links and wants the article drafted, reviewed, polished, and finalized into a new Markdown file without overwriting the original.
version: 1.0.0
user-invocable: true
---

# Article Review Orchestrator

Turn an existing article draft or an article topic into a reviewed, humanized, publication-ready Markdown article by orchestrating `brainstorming`, `humanizer`, and `mermaid-share`.

## When to use

Use this skill when the user:

- provides a finished or partial article and wants it reviewed or polished
- provides only an article title/topic plus several reference links and wants a complete article
- wants a blog post to sound less AI-generated
- wants Mermaid diagrams inside an article converted into hosted SVG embeds
- wants the final result saved as a new Markdown file instead of overwriting the source

## Input modes

This skill supports two starting points:

1. **Existing article mode**
   - The user provides a Markdown article file or pasted article content.
2. **Topic-and-sources mode**
   - The user provides an article topic/title, optional constraints, and one or more reference links.

## Workflow

1. Identify which input mode applies.
2. Read the source article if a file was provided. If the article was pasted inline, use that text directly.
3. If the user only provided a topic and reference links, first collect the topic, audience, tone, constraints, and sources from the request.
4. Invoke `brainstorming` first.
5. Use `brainstorming` to define how the article should be reviewed or written before drafting or editing prose.
   - For existing article mode, define the review rubric: audience, intent, structure, tone, accuracy expectations, and what should be preserved.
   - For topic-and-sources mode, define the writing plan: article angle, audience, outline, source usage, and success criteria.
6. Produce the full article text according to the `brainstorming` result.
   - If starting from an existing article, revise it according to the agreed review approach.
   - If starting from a topic and references, draft the article first and then refine it into a full Markdown article.
7. Invoke `humanizer` on the full article body to remove AI writing patterns while preserving meaning, accuracy, citations, and intended tone.
8. Scan the resulting Markdown for Mermaid fenced code blocks. A Mermaid block is any fenced code block whose language tag is `mermaid`.
9. Process Mermaid blocks one by one, in document order.
   - For each Mermaid block, invoke `mermaid-share`.
   - Use the exact Mermaid code block contents as input.
   - If the user expressed a preference about theme or opaque background, pass that preference through the `mermaid-share` workflow.
   - If `mermaid-share` succeeds, replace the entire Mermaid fenced block with the returned Markdown embed string.
   - If `mermaid-share` reports unsupported diagram type or upload failure for one block, leave that block in place, continue processing the remaining Mermaid blocks, and report the failure in the final summary.
10. Save the finished article as a new Markdown file named `<article-title>-reviewed.md`.
11. Never overwrite the original article file.

## File naming

Derive the output filename from the article title.

- Prefer the article's top-level Markdown heading if present.
- Otherwise use the user-provided title.
- Otherwise infer a concise title from the article topic.
- Slugify the title for the filename.
- Save as `<article-title>-reviewed.md` in the same directory as the source article when starting from an existing file.
- If there is no source file, save the new file in the current working area using the derived filename.
- If `<article-title>-reviewed.md` already exists, do not overwrite it. Save to `<article-title>-reviewed-2.md`, `<article-title>-reviewed-3.md`, and so on.

## Output

Return:

- the path to the new reviewed Markdown file
- a short summary of what changed
- how many Mermaid blocks were found
- how many Mermaid blocks were successfully replaced with hosted SVG embeds
- any Mermaid blocks that could not be converted

## Rules

- Invoke `brainstorming` before making substantive editorial decisions.
- Invoke `humanizer` after the article structure and content are settled.
- Invoke `mermaid-share` only after the article text is otherwise finalized.
- Treat every Mermaid fenced block independently; a single article may contain multiple Mermaid diagrams.
- Replace Mermaid blocks with the Markdown embed returned by `mermaid-share`, not with raw URLs unless the user asks otherwise.
- Preserve valid non-Mermaid Markdown exactly unless you are editing it as part of the review or writing pass.
- Keep citations, factual claims, and source attributions intact when humanizing.
- Never overwrite the original file.
- If the user provided only a topic and links, produce a full article before saving the reviewed file.
- If the user asks only for review feedback and explicitly does not want rewriting, stop after the `brainstorming` review plan and provide the review instead of rewriting the article.

## Agent notes

- Prefer existing article mode when both a draft and a topic are present.
- If the source article is not Markdown, convert it into Markdown before the humanization and Mermaid replacement steps.
- For blog and documentation publishing contexts, prefer transparent Mermaid SVG output unless the user explicitly asks to preserve the theme background.
- When multiple Mermaid blocks exist, keep their replacement order stable so the surrounding prose remains aligned with the correct diagram.

## Example outcomes

**Example 1: Existing article**
- Input: `draft.md` containing a technical blog post with two Mermaid diagrams.
- Outcome: review strategy via `brainstorming` → prose polish via `humanizer` → each Mermaid block uploaded via `mermaid-share` → saved as `my-title-reviewed.md`.

**Example 2: Topic plus references**
- Input: an article title, several reference URLs, and desired audience.
- Outcome: article plan via `brainstorming` → full draft written → humanized → any Mermaid diagrams processed → saved as `<article-title>-reviewed.md`.
