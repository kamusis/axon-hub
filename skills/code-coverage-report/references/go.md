# Go Coverage Reference

Use this reference for Go projects.

## Detection

Look for:

- `go.mod`
- `go.work`
- `*_test.go` files
- Makefile or CI test commands
- Existing `coverage.out` or coverage upload steps

Prefer documented project commands when present.

## Common Tools

Go has built-in coverage tooling:

```bash
go test
go tool cover
```

External tools may appear in CI, but built-in coverage is usually enough for a first report.

## Commands

Run all packages:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

Generate HTML:

```bash
go tool cover -html=coverage.out -o coverage.html
```

Run a package only:

```bash
go test ./path/to/package -coverprofile=coverage.out
go tool cover -func=coverage.out
```

Include cross-package coverage for integration-style tests:

```bash
go test ./... -coverpkg=./... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

## Report Files

Typical files:

```text
coverage.out
coverage.html
```

These are usually generated artifacts. Check `.gitignore` before leaving them in the worktree.

## Parsing Reports

Function summary:

```bash
go tool cover -func=coverage.out
```

Show lowest-covered functions:

```bash
go tool cover -func=coverage.out |
  awk '/%$/ && $3 != "100.0%" { print }' |
  sort -k3 -n |
  head
```

Total coverage:

```bash
go tool cover -func=coverage.out | awk '/^total:/ { print }'
```

## Interpretation

Go coverage is function-oriented in terminal output. HTML is better for line-level review.

High-signal gaps often include:

- Error returns.
- Context cancellation and timeout handling.
- HTTP handler status and response body behavior.
- CLI flag parsing and command output.
- File persistence and config loading.
- Boundary clients that construct requests or translate errors.
- Resource cleanup with `Close`, `defer`, goroutines, channels, locks, and background workers.

Lower-signal gaps often include:

- `main()`.
- Thin wrappers around standard library calls.
- Generated code.
- Defensive branches that are unreachable under current invariants.

## Common Pitfalls

- `go test ./...` reports each package separately; a package with no tests may show 0%.
- Without `-coverpkg`, tests in one package may not count coverage for imported sibling packages.
- Parallel tests can hide race-related lifecycle gaps; coverage does not replace `go test -race`.
- Table-driven tests can cover many cases, but weak assertions still produce weak protection.
- Do not add tests for unexported helpers when exported behavior can trigger the same path.
