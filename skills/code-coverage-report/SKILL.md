---
name: code-coverage-report
description: Use when the user asks to run, analyze, summarize, compare, or generate code coverage reports for any repository. Detect the project's languages and test tools, run the appropriate coverage commands, and produce an actionable report with coverage evidence, high-risk gaps, and next steps. Use this before coverage-driven-test-improvement when tests need to be added from coverage evidence.
---

# Code Coverage Report

## Purpose

Generate a clear, actionable code coverage report for the repository in front of you.

Coverage answers "what code did tests execute?" It does not prove that tests assert the right behavior. Treat coverage as a blind-spot detector, then connect those blind spots to product, API, safety, reliability, or maintainability risk.

## When To Use

Use this skill when the user asks to:

- Run coverage.
- Check test coverage.
- Generate or interpret a coverage report.
- Compare coverage between components.
- Identify uncovered files, lines, branches, or functions.
- Decide what coverage gaps matter.

If the user asks to add tests based on the report, use `coverage-driven-test-improvement` after generating the report.

## Workflow

### 1. Identify Project Components

Inspect the repository before running coverage.

Look for:

- Build files: `pom.xml`, `build.gradle`, `go.mod`, `package.json`, `pyproject.toml`, `requirements.txt`, `.csproj`, `Cargo.toml`, etc.
- Existing test commands in README, CI workflows, Makefiles, scripts, or task runners.
- Existing coverage config or artifacts.
- Monorepo boundaries and independently tested packages.

Do not assume "frontend" or "backend" from language alone. A repository can have Java services, Go CLIs, TypeScript frontends, Python workers, Rust libraries, or mixed components.

### 2. Detect Coverage Tooling

Prefer the repository's existing coverage tooling. Do not replace it just because another tool is familiar.

When a component uses one of these ecosystems, read only the matching reference file:

| Ecosystem | Reference |
| --- | --- |
| Java | `references/java.md` |
| Go | `references/go.md` |
| JavaScript/TypeScript | `references/javascript-typescript.md` |
| Python | `references/python.md` |
| .NET | `references/dotnet.md` |
| Rust | `references/rust.md` |

If tooling is missing, report the gap and recommend setup. Do not invent coverage numbers.

### 3. Verify Required Tools

Check only the tools needed for the detected components.

Examples:

- Java: `java -version`, `mvn -version`, or `./gradlew --version`.
- Go: `go version`.
- JavaScript/TypeScript: `node --version`, package manager version, and project scripts.
- Python: `python --version` or `python3 --version`, plus test runner availability.
- .NET: `dotnet --info`.
- Rust: `rustc --version`, `cargo --version`.

If a tool is missing, skip that component's run and list it under blockers.

### 4. Run Coverage

Run coverage component by component. Use the narrowest command that produces a trustworthy report for that component.

Capture:

- Exact command.
- Pass/fail status.
- Test count or failure summary if available.
- Report paths.
- Total coverage numbers.
- Per-package/file/function gaps when available.

Do not change production code while generating a report. Do not add tests in this skill.

### 5. Extract Useful Numbers

Do not stop at a single total percentage. Extract the metrics the tool provides:

- Line or statement coverage.
- Branch coverage.
- Function or method coverage.
- Instruction coverage if available.
- File/package/module coverage.
- Uncovered lines or branches.

When a tool reports several metrics, explain what each means. Branch coverage is often more revealing than line coverage for error handling and policy logic.

### 6. Separate Signal From Noise

Coverage reports often include code that is not worth direct testing.

Likely high-signal gaps:

- Security and permission checks.
- Validation and error handling.
- Persistence, serialization, migration, and recovery.
- External boundary adapters and error translation.
- Resource lifecycle, cleanup, retry, timeout, and cancellation.
- Public API, command, or UI behavior.
- Domain-specific branching.

Likely lower-signal gaps:

- Generated code.
- Plain data carriers with no behavior.
- Framework bootstrap or dependency wiring.
- Trivial getters, setters, builders, enum plumbing.
- Defensive guards that are unreachable under current invariants.

Do not automatically dismiss low-signal areas. If they contain validation, compatibility mapping, redaction, or security behavior, classify them as real gaps.

### 7. Prioritize By Risk

Rank gaps by risk, not by raw missed lines.

Use this general order:

1. Safety, security, permissions, secrets, and unsafe operations.
2. Public contracts: APIs, commands, UI behavior, file formats, machine-readable output.
3. Persistence, migration, reload, recovery, and corrupt input.
4. External boundaries: network, database, filesystem, subprocesses, SDKs.
5. Stateful lifecycle: pools, sessions, locks, handles, classloaders, cleanup.
6. Domain branching: parsers, routers, normalizers, rule engines, feature flags.
7. Presentation/formatting, when output is a contract.
8. Generated or framework code, usually deferred.

### 8. Produce The Report

Use this format:

```markdown
## Coverage Report

### Commands Run
- `[command]` — passed/failed, important notes

### Summary
| Component | Main metric | Branch metric | Report |
| --- | ---: | ---: | --- |

### High-Risk Gaps
| Priority | Area | Evidence | Why it matters | Suggested next test |
| --- | --- | --- | --- | --- |

### Lower-Risk Or Intentional Gaps
- `[area]`: `[reason]`

### Blockers Or Missing Tools
- ...

### Recommended Next Actions
1. ...
2. ...
3. ...
```

If a metric is unavailable, write `n/a` and explain why.

## Important Constraints

- Never claim coverage passed without fresh command output.
- Never invent coverage percentages.
- Do not add tests or change production code while generating the report.
- Prefer existing project commands over generic examples.
- Keep generated coverage artifacts unless the user asks to clean them up or they are clearly temporary.
- If the report is from a remote machine and HTML is inconvenient, parse text, XML, CSV, JSON, or terminal summaries instead.
