# Skill Repo Survey Notes

Dated: 2026-05-08

## mattpocock/skills

Repo: https://github.com/mattpocock/skills

Contains diagnosed SKILL.md from mattpocock's Zettelkasten-style skill system. Notable entries:

- **diagnose** — The core skill. Teaches building explicit feedback loops as the primary debugging strategy. Key ideas:
  - Feedback loops are the fundamental unit of debugging, not hypothesis testing
  - "When stuck, build a smaller loop" principle
  - 10+ loop construction patterns (print loop, diff loop, bisect loop, etc.)
  - Non-deterministic bug strategies
  - Multi-hypothesis ranked approach (3-5 ranked hypotheses, user confirms before testing)

Relevant content was merged into `systematic-debugging` skill (Phase 1: Build Feedback Loop).

## addyosmani/agent-skills

Repo: https://github.com/addyosmani/agent-skills

Agent evaluation framework with:
- Structured rubric for assessing agent quality
- Multiple assessment dimensions
- Evaluation methodology documentation

## Action Items

- [ ] Full survey of both repos to identify which specific skills are worth adopting
- [ ] Compare mattpocock's diagnose feedback-loop taxonomy against existing systematic-debugging phases
- [ ] Evaluate whether addyosmani's agent-skills rubric can enhance the systematic-debugging skill's agent evaluation guidance
