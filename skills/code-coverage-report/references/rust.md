# Rust Coverage Reference

Use this reference for Rust projects.

## Detection

Look for:

- `Cargo.toml`
- `Cargo.lock`
- Cargo workspace members
- `tests/` integration tests
- `benches/`
- CI steps using `cargo llvm-cov`, `grcov`, or `cargo tarpaulin`

Prefer existing CI or Makefile commands when present.

## Common Tools

Common Rust coverage tooling:

- `cargo llvm-cov`
- `cargo tarpaulin`
- `grcov` with LLVM profiling

`cargo llvm-cov` is a common modern default when available.

## Commands

With cargo-llvm-cov:

```bash
cargo llvm-cov
cargo llvm-cov --html
cargo llvm-cov --lcov --output-path lcov.info
```

For workspaces:

```bash
cargo llvm-cov --workspace
cargo llvm-cov --workspace --html
```

With tarpaulin:

```bash
cargo tarpaulin
cargo tarpaulin --out Html
cargo tarpaulin --out Xml
```

Run tests normally first if coverage setup is unknown:

```bash
cargo test
```

## Report Files

Common output paths:

```text
target/llvm-cov/html/index.html
lcov.info
cobertura.xml
tarpaulin-report.html
```

## Parsing Reports

For LCOV:

```bash
rg -n '^(SF|DA|BRDA|LF|LH|BRF|BRH):' lcov.info
```

For terminal output, capture the summary from the coverage command.

## Interpretation

High-signal gaps often include:

- Error variants and `Result` handling.
- Parsing and validation.
- Feature-flagged behavior.
- Async cancellation and task lifecycle.
- Resource cleanup and `Drop` behavior.
- Unsafe blocks and FFI boundaries.
- Serialization/deserialization and compatibility.
- Public library API contracts.

Lower-signal gaps often include:

- Derived trait implementations.
- Simple newtype wrappers with no validation.
- Build scripts unless they contain meaningful logic.
- Platform-specific branches irrelevant to the current target.

## Feature Flags And Targets

Coverage may change significantly by feature flag or target. Inspect:

```bash
cargo test --all-features
cargo test --no-default-features
cargo test --features <feature>
```

Coverage commands often support equivalent feature flags:

```bash
cargo llvm-cov --all-features
cargo llvm-cov --no-default-features
```

## Common Pitfalls

- Workspace reports may miss crates if not run with workspace flags.
- Feature-gated code may appear uncovered because the feature was not enabled.
- Platform-specific code may be legitimately uncovered on the current OS.
- Async and concurrent behavior needs assertions about outcomes, not just execution.
- Unsafe/FFI code may need boundary-focused tests or explicit documentation if impractical to cover.
