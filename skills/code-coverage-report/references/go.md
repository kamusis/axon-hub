# Go Coverage Reference

Use this reference for Go projects.

## Detection

Look for:

- `go.mod`
- `go.sum`
- `go.work`
- `*_test.go` files
- Makefile or CI test commands
- Existing `coverage.out` or coverage upload steps
- Service boundaries such as `cmd/`, `internal/`, `pkg/`, HTTP handlers, middleware, repositories, workers, and CLIs.

Prefer documented project commands when present.

## Backend Service Strategy

For Go backend services, report coverage at package level first, then connect low-coverage packages to service risk. Go's terminal coverage output is useful for quick totals, but package names alone rarely explain whether the gap is important.

Use this order:

1. Identify commands, libraries, and service packages.
2. Run the documented Go test or coverage command if present.
3. If no coverage command exists, use Go's built-in coverage tooling.
4. Decide whether package-local coverage is enough or whether `-coverpkg=./...` is needed to reflect integration-style tests.
5. Keep the chosen coverage mode explicit in the report because `-coverpkg` changes the denominator and can produce different totals.

Do not default to tests that require live databases, network services, cloud credentials, or long-running daemons unless the repository documents that environment. If such tests are required for meaningful coverage, list the environment as a blocker or separate integration coverage scope.

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

Run a focused package when broad coverage fails for environmental reasons:

```bash
go test ./internal/example -coverprofile=coverage.out
go tool cover -func=coverage.out
```

Use the real package path from the repository.

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
- Authentication, authorization, HMAC/signature checks, session, token, and middleware branches.
- Repository, storage, transaction, migration, and serialization error paths.
- CLI flag parsing and command output.
- File persistence and config loading.
- Worker, scheduler, webhook, queue, and background task behavior.
- Boundary clients that construct requests or translate errors.
- Resource cleanup with `Close`, `defer`, goroutines, channels, locks, and background workers.

Lower-signal gaps often include:

- `main()`.
- Thin wrappers around standard library calls.
- Generated code.
- Dependency injection or route wiring that only registers handlers.
- Defensive branches that are unreachable under current invariants.

## Common Pitfalls

- `go test ./...` reports each package separately; a package with no tests may show 0%.
- Without `-coverpkg`, tests in one package may not count coverage for imported sibling packages.
- With `-coverpkg`, generated files, command packages, or framework wiring can lower totals without indicating product risk. Explain this when prioritizing gaps.
- Parallel tests can hide race-related lifecycle gaps; coverage does not replace `go test -race`.
- Table-driven tests can cover many cases, but weak assertions still produce weak protection.
- Do not add tests for unexported helpers when exported behavior can trigger the same path.
- Mock-heavy service tests can execute branches without proving database, HTTP, or filesystem contracts. Note when confidence depends on mocks.
