# Workspace Navigation & Layout Conformance

Workspace navigation and layout governance ensure unified information architecture, keyboard accessibility, and adherence to Mopheus container and PageHeader standards.

## Sub-features

- `workspace-sidebar`: Render persistent collapsible sidebar containing Tickets, Topics, Projects, Agents, Teams, Channels, and Settings.
- `workspace-switcher`: Switch active workspace via top sidebar dropdown without full-page flash.
- `container-layout-standard`: Enforce outer padding (`p-4 sm:p-6`) and inner rounded card container (`flex flex-1 min-h-0 flex-col overflow-hidden rounded-lg border bg-background`).
- `page-header-standard`: Enforce single-line PageHeader layout (`[Icon (h-4 w-4 text-muted-foreground)] [Title (text-sm font-medium)] [Count (font-mono text-xs)] [Inline Tagline]`).
- `anti-flicker-url-sync`: Verify URL state updates via `window.history.replaceState` without triggering App Router Suspense skeleton flashes.

## How to get to it (user POV)

- Open any workspace route: `/dev-space/tickets`, `/dev-space/projects`, `/dev-space/agents`.
- Click the workspace switcher at top-left to switch between workspaces.
- Click sidebar links to navigate between core views.
- Use `Cmd/Ctrl + K` to trigger quick search.

## Driving it with verify-mopheus

Preconditions:
- Preview harness is healthy (`~/.gemini/config/skills/verify-mopheus/scripts/doctor.sh` passes).

### Step 1: Capture Sidebar and Header on Main Tickets View
```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/tickets" \
  --output "/tmp/verify-layout-tickets.png"
```
*Observable Result*: Generates screenshot confirming single-line `PageHeader` (Tickets icon, `font-medium` title, tabular count, inline tagline) and unified card container.

### Step 2: Capture Projects View Navigation
```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/projects" \
  --output "/tmp/verify-layout-projects.png"
```
*Observable Result*: Generates screenshot verifying navigation to `/dev-space/projects` with identical container styling and toolbar enclosed in `border-b px-4`.

### Step 3: Capture Settings View Navigation
```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/settings" \
  --output "/tmp/verify-layout-settings.png"
```
*Observable Result*: Generates screenshot verifying settings panel rendering with tab navigation.

## Gotchas

- **Header Font Rule**: `PageHeader` titles must strictly use `font-medium`, NEVER `font-semibold`. Subtitles stay inline.
- **Destructive Action Safety**: Resource rows must NEVER render raw destructive buttons on hover. All delete/archive actions require Radix `AlertDialog` confirmation with frosted glass overlay.
- **No Chevron Decorators**: Do not append decorative `>` chevrons to list rows.
- **URL Synchronization**: Client-side filtering/sorting must sync via `window.history.replaceState` to avoid Next.js `_rsc` roundtrips.
