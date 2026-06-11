# .NET Coverage Reference

Use this reference for .NET projects.

## Detection

Look for:

- `.sln`
- `.csproj`, `.fsproj`, or `.vbproj`
- `Directory.Build.props`
- `global.json`
- `*.Tests` projects
- Existing CI coverage steps
- Coverlet, ReportGenerator, or XPlat coverage configuration

Prefer project scripts and CI commands when present.

## Common Tools

Common .NET coverage tooling:

- `dotnet test --collect:"XPlat Code Coverage"`
- coverlet collector
- coverlet.msbuild
- ReportGenerator for readable HTML reports

## Commands

XPlat Code Coverage:

```bash
dotnet test --collect:"XPlat Code Coverage"
```

For a solution:

```bash
dotnet test <solution>.sln --collect:"XPlat Code Coverage"
```

With coverlet.msbuild:

```bash
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura
```

With multiple formats:

```bash
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=\"json,cobertura,opencover\"
```

Generate HTML if ReportGenerator is available:

```bash
reportgenerator -reports:"**/coverage.cobertura.xml" -targetdir:"coveragereport"
```

## Report Files

Common output paths:

```text
TestResults/<guid>/coverage.cobertura.xml
coverage.cobertura.xml
coverage.json
coverage.opencover.xml
coveragereport/index.html
```

## Parsing Reports

Cobertura XML exposes line-rate and branch-rate:

```bash
rg -n 'line-rate|branch-rate|filename=' TestResults coverage.cobertura.xml
```

If using coverlet JSON:

```bash
cat coverage.json
```

## Interpretation

High-signal gaps often include:

- Controllers, minimal API endpoints, handlers, and middleware.
- Authorization policies and claims handling.
- Validation and model binding errors.
- Persistence repositories and migrations.
- Options/configuration loading and invalid configuration handling.
- Background services, cancellation tokens, and hosted service lifecycle.
- HTTP clients and external service error translation.

Lower-signal gaps often include:

- Auto-generated code.
- Plain POCOs or records with no validation.
- Dependency injection registration.
- Program startup boilerplate.
- Designer-generated files.

## Common Pitfalls

- Coverage may be split across many `TestResults` directories.
- Different test projects may need merged reports.
- Generated files may need exclusion through runsettings or coverlet filters.
- Async code needs tests for cancellation and failure paths.
- Mocking repositories or clients too broadly can hide real behavior.
- Branch coverage may reveal missing error handling even when line coverage looks high.
