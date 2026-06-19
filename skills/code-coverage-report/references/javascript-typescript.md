# JavaScript And TypeScript Coverage Reference

Use this reference for JavaScript and TypeScript projects, including Node services, CLIs, libraries, and frontend apps.

## Detection

Look for:

- `package.json`
- `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, or `bun.lockb`
- Test config: `jest.config.*`, `vitest.config.*`, `nyc.config.*`, `cypress.config.*`, `playwright.config.*`
- Existing scripts: `test`, `test:coverage`, `coverage`, `unit`, `vitest`, `jest`
- TypeScript config: `tsconfig.json`
- Workspace and monorepo config: `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, or package manager workspaces.
- Framework boundaries: frontend apps, Node services, shared packages, CLIs, documentation apps, and generated content packages.

Prefer package scripts over direct tool invocation. In workspaces, inspect the root scripts and the relevant package scripts before running coverage; the root command may only delegate tests or may skip packages without a `test` script.

## Monorepo And Frontend Package Strategy

For JavaScript/TypeScript monorepos, report coverage by package or app instead of collapsing everything into one number.

Use this order:

1. Identify the package manager and workspace runner.
2. List packages that contain source files, tests, or test configs.
3. Separate frontend apps, backend services, shared libraries, CLIs, and documentation-only packages.
4. Run the package's documented coverage script when it exists.
5. If only a plain test script exists, check whether the local test runner supports a coverage flag.
6. If coverage dependencies or config are missing, report a tooling gap instead of installing dependencies or inventing numbers.

For frontend frameworks such as Next.js, Vite, Remix, Astro, or React component libraries, distinguish unit/component coverage from browser or end-to-end coverage. Unit coverage can reveal uncovered hooks, stores, API clients, route helpers, and component states, but it does not prove the rendered app works in a real browser unless the project has browser or e2e coverage instrumentation.

## Common Tools

Common coverage engines:

- Jest coverage, usually powered by V8 or Babel instrumentation.
- Vitest coverage with `@vitest/coverage-v8` or `@vitest/coverage-istanbul`.
- nyc/Istanbul for Node and older setups.
- c8 for V8 coverage.
- Playwright/Cypress coverage only when the project is explicitly configured for browser coverage.

## Commands

Inspect scripts first:

```bash
npm run
```

Common commands:

```bash
npm test -- --coverage
npm run test -- --coverage
npm run test:coverage
npx jest --coverage
npx vitest run --coverage
npx nyc npm test
npx c8 npm test
```

Use the detected package manager:

```bash
pnpm test -- --coverage
yarn test --coverage
bun test --coverage
```

Workspace runners often support filtered package execution. Prefer the project's documented form, for example:

```bash
pnpm --filter <package-name> test -- --coverage
turbo test --filter=<package-name>
nx test <project-name> --coverage
```

Treat these as patterns, not defaults. Confirm the actual package names and scripts from the repository before running them.

## Report Files

Common output paths:

```text
coverage/lcov-report/index.html
coverage/lcov.info
coverage/coverage-final.json
coverage/clover.xml
coverage/cobertura-coverage.xml
```

Vitest may also produce:

```text
coverage/index.html
```

Coverage output may be package-local or repository-rooted depending on the runner. Record the exact path and component that produced it.

## Parsing Reports

Terminal summaries are often enough for a first pass.

LCOV can be inspected textually:

```bash
rg -n '^(SF|DA|BRDA|LF|LH|BRF|BRH):' coverage/lcov.info
```

Files with low line coverage can often be derived from LCOV `LF` and `LH` totals.

If `coverage-summary.json` exists:

```bash
cat coverage/coverage-summary.json
```

## Interpretation

JavaScript/TypeScript coverage often mixes:

- Source files.
- Generated or compiled artifacts.
- Framework entry points.
- UI components.
- Hooks, stores, routes, API clients, and server handlers.

High-signal gaps often include:

- Request handlers and API clients.
- Authentication, authorization, and route guards.
- Form validation and error states.
- State management branches.
- Serialization/deserialization and compatibility mapping.
- Retry, timeout, and cancellation logic.
- CLI commands and argument parsing.
- UI behavior visible to users, especially disabled states, loading states, and error rendering.
- Server actions, route handlers, loaders, and API route error contracts when the framework exposes them.
- Workspace-shared packages that define schemas, SDK clients, permissions, formatting contracts, or persistence adapters.

Lower-signal gaps often include:

- Barrel files such as `index.ts`.
- Static constants.
- Generated types.
- Framework bootstraps.
- Documentation-only apps or content packages with no executable behavior.
- Storybook-only files unless they contain behavior.

## Frontend Notes

Unit/component coverage does not prove that the browser experience works. If uncovered behavior is interaction-heavy, prefer component tests with user events or e2e tests if the project already uses them.

Be careful with snapshots. Snapshot coverage can execute code without proving behavior. Prefer assertions about visible text, roles, state changes, emitted events, or API calls.

## Common Pitfalls

- Coverage may include build output if include/exclude patterns are wrong.
- Type-only files can distort TypeScript coverage reports.
- jsdom tests can miss browser layout and canvas behavior.
- E2E coverage usually requires explicit instrumentation and is not automatic.
- Mocking all child components may hide the behavior that should be tested.
- A root monorepo test command may pass even when some packages have no test or coverage script.
- Vitest coverage requires a coverage provider package such as V8 or Istanbul. If it is absent, report the missing tooling rather than changing dependencies during the audit.
- Frontend route and component coverage can be inflated by render-only tests with weak assertions. Mention assertion quality when it affects confidence.
