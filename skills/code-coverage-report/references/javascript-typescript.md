# JavaScript And TypeScript Coverage Reference

Use this reference for JavaScript and TypeScript projects, including Node services, CLIs, libraries, and frontend apps.

## Detection

Look for:

- `package.json`
- `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, or `bun.lockb`
- Test config: `jest.config.*`, `vitest.config.*`, `nyc.config.*`, `cypress.config.*`, `playwright.config.*`
- Existing scripts: `test`, `test:coverage`, `coverage`, `unit`, `vitest`, `jest`
- TypeScript config: `tsconfig.json`

Prefer package scripts over direct tool invocation.

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

Lower-signal gaps often include:

- Barrel files such as `index.ts`.
- Static constants.
- Generated types.
- Framework bootstraps.
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
