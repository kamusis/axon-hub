---
name: anatomy
description: Build industrial-grade, interactive 3D isometric CAD exploded-view diagrams, mechanical cutaway illustrations, and printable A4 engineering blueprints (HTML + SVG + PDF + PNG). Translates any physical machine, hardware device, or software architecture into a dense, physical multi-assembly mechanism with lathe-turned bodies, 3D routed pipes/harnesses, spring-physics explosion, numbered callout pins, BOM tables, and circular loupe close-ups.
---

# Anatomy — Industrial Isometric CAD & Engineering Blueprint Engine

Build figures like an aerospace propulsion rig or precision instrument on an inspection bench: a heavy slotted bedplate on mounts, lathe-turned housings and flanges, multi-stage rotors, 3D routed manifolds and braided harnesses, ruler strips with tick marks, and a live telemetry readout. Even abstract software architectures (consensus engines, rate limiters, storage engines, schedulers) are explained by inventing a concrete physical machine whose mechanism maps 1-to-1 onto the concept.

---

## 1. Bundled Layout & Clean Build Workspace Rule

This skill ships self-contained with its complete CAD kernel, headless Chrome verification suite, A4 blueprint printer, and flagship reference model:

| Path | Purpose |
| --- | --- |
| `kit/iso-kit.mjs` & `kit/iso.css` | Core isometric camera (`createProjection`, `fitProjection`), slabs, extrusions, ticks, springs, SVG/HTML page builders (`pageHtml`, `plateHtml`, `figureSvg`). |
| `kit/lathe.mjs` | Rotational bodies along any 3D axis (`frameOf`, `frameAlong`, `lathe`, `solidOf`, `disc`, `ringBand`, `sphereOf`, `saddleOf`, `bandsOf`, `ribsOf`, `dotsOf`, `rodOut`, `fillet`). |
| `kit/tube.mjs` | 3D pipes, manifolds, and braided cable harnesses (`tubePieces`, `tubeSvg`, `crossingsOf`, `runsOf`) with automatic collar gaps and cross-section rings. |
| `kit/audit.mjs` | Painter's order ray-caster and geometry auditor (`recorder`, `settle`, `auditOrExit`, `slide`). |
| `kit/pdf-button.mjs` | Corner PDF badge (`pdfButton(href)`) linking the interactive plate to its printable A4 sheet. |
| `scripts/print.mjs` & `scripts/print-sheet.mjs` | Renders `sheet.mjs` into printable A4/Letter engineering PDFs and preview PNGs (`--format drawing\|detailed\|poster\|all --png`). |
| `scripts/capture.mjs` & `scripts/drive.mjs` | Headless Chrome screenshot, zoom crop, console error check, and scripted interaction driver. |
| `scripts/lines.mjs` | Verifies that every texture line ends cleanly on a stroke, dot, or outline. |
| `examples/gas-turbine/` | **Flagship Reference (`GT-400 Horizontal Industrial Turboshaft Skid`)**: 367 3D items across 10 coaxial/radial exploding sub-assemblies (`build.mjs`, `gt.css`, `live.js`, `sheet.mjs`). Always read `examples/gas-turbine/build.mjs` and `examples/gas-turbine/sheet.mjs` before starting a complex build. |

### Clean Build Workspace Rule (Mandatory)
**Never write generated `.html`, `.pdf`, or `.png` files inside the installed `skills/anatomy/` directory.** Always stage a clean working directory under `/tmp/anatomy-<slug>` (or the task's scratch directory) that symlinks `kit` and `scripts` from this skill directory:

```bash
SKILL_DIR="<path-to-this-anatomy-skill-dir>"
WORK_DIR="/tmp/anatomy-<slug>"
rm -rf "$WORK_DIR" && mkdir -p "$WORK_DIR/examples/<slug>"
ln -s "$SKILL_DIR/kit" "$WORK_DIR/kit"
ln -s "$SKILL_DIR/scripts" "$WORK_DIR/scripts"
```

That keeps imports in `examples/<slug>/build.mjs` (`import * as k from "../../kit/iso-kit.mjs"`) identical to `examples/gas-turbine/build.mjs`.

---

## 2. Complexity & Craft Bar

Every figure must look like a real industrial assembly drawing, never a sparse collection of boxes:

1. **Multi-Assembly Exploded Architecture (6–10 Sub-Assemblies)**
   - Partition the machine into **6 to 10 distinct functional sub-assemblies** (plus `stand` / bedplate), each tagged with `data-part="<id>"` and assigned a clean 3D explosion vector `move: [dx, dy, dz]`.
   - For coaxial machinery along a primary axis (e.g., `MAIN = G.frameOf([0, 0, z], [1, 0, 0], [0, 1, 0], [0, 0, 1])`), explode core stages coaxially along `±X`, flanking skids radially along `±Y`, and top manifolds/controllers upward along `+Z` so no assemblies collide or occlude each other when apart.
2. **Rich Mechanical Vocabulary (150–400+ 3D Items)**
   - **Bedplate & Mounts**: Slotted structural baseplate (`k.slabOf`), vibration isolator feet, corner bolt rings (`k.ringOf`), engraved ruler strips (`k.topTicks`, `k.sideTicks`), and pedestal trunnions.
   - **Turned & Flanged Assemblies (`kit/lathe.mjs`)**: Multi-stepped housings with smooth profile knots (`[s, r, 1]`), bolted mating flanges (`G.dotsOf` with `fade`), axial rotor blade stages, cooling fins (`G.ribsOf` with `seams: true`), sight glasses, and conical fluted stacks.
   - **3D Piping & Harnesses (`kit/tube.mjs`)**: Route pipes and cables with `G.fillet(waypoints, radius)`, wrap them with mounting clamps/collars (`gaps`), add braided or corrugated rings (`rings`), and land every pipe end on a real flange, boss, or manifold block.
3. **Four-Tone Shading & Single Lit Focus**
   - Base and mounts use `lo`, structural housings use `mid`, primary working mechanisms use `hi`, and active/energized elements use `lit`.
   - Every solid is opaque paper-filled (`iso-fill`) and painted back-to-front so nearer parts cleanly occlude parts behind them.
4. **Fast Painter's Order Settlement (`< 1s` Build Time)**
   - Record all solids and tubes in `const R = A.recorder(P, { order: PART_IDS, spring: SPRING })`.
   - Solve depth ordering across both assembled (`0`) and exploded (`1`) states with:
     ```js
     A.settle(R, P, { states: [0, 1], step: 0.6 });
     ```
     *(Do not omit `{ states: [0, 1], step: 0.6 }` on 300+ item models, or `settle` will rasterize 60 spring sub-frames at `step: 0.25` and take >60 seconds.)*

---

## 3. End-to-End Build, Print & Verification Workflow

### Step 1 — Build Standalone Light & Dark Interactive HTML
Write `examples/<slug>/build.mjs`, `<slug>.css`, and `live.js` following `examples/gas-turbine/`:
- Include `pdfButton("<slug>-drawing-a4.pdf")` inside the plate body.
- Support hover / `Space` to toggle the exploded view, `01..N` legend buttons to isolate/focus individual assemblies, and an interactive operating button (e.g., `Start Turbine` / `Inject Burst`) that updates the live corner readout.
- Build both themes:
  ```bash
  node "$WORK_DIR/examples/<slug>/build.mjs"
  node "$WORK_DIR/examples/<slug>/build.mjs" --light
  ```
  This outputs standalone, zero-dependency `<slug>.html` (dark) and `<slug>-light.html` (light) with all CSS, SVG, and spring physics inlined.

### Step 2 — Generate A4 Engineering Blueprints (`sheet.mjs` + `scripts/print.mjs`)
Write `examples/<slug>/sheet.mjs` defining:
- `page`: `"./<slug>-light.html"`
- `poses`: `assembled` (`[["eval", "window.__setExplode && window.__setExplode(0)"]]`) and `apart` (`[["eval", "window.__setExplode && window.__setExplode(1)"]]`)
- `parts`: numbered callout pins (`id`, `name`, `select: '[data-part="..."]'`, `detail`)
- `spec`: 6–8 true engineering specification rows
- `steps`: 4–6 sequential operating states with `lit` part highlights
- `assemblies`: 4 functional subsystem groups
- `closeups`: 3 circular high-magnification loupes (`A`, `B`, `C`)

Render all A4 engineering sheets (PDF + high-res PNG previews):
```bash
node "$WORK_DIR/scripts/print.mjs" "$WORK_DIR/examples/<slug>/sheet.mjs" --format all --png
```
This produces:
- `<slug>-drawing-a4.pdf` & `<slug>-drawing-a4.png` (1-page technical blueprint with numbered callout pins, BOM table, spec block, assembled inset, and step strip)
- `<slug>-detailed-a4.pdf` & `<slug>-detailed-a4.png` (multi-page engineering breakdown with circular loupes `A/B/C`, step-by-step sequence, and assembly cards)
- `<slug>-poster-a4.pdf` & `<slug>-poster-a4.png` (1-page large-format exploded poster)

### Step 3 — Capture Assembled & Exploded Screenshots and Verify Visually
Capture both assembled and exploded states in light and dark themes and verify `console: clean` and `scrolls sideways: no`:
```bash
node "$WORK_DIR/scripts/capture.mjs" "$WORK_DIR/examples/<slug>/<slug>-light.html" --out "$WORK_DIR/shots/assembled-light.png"
node "$WORK_DIR/scripts/drive.mjs" "$WORK_DIR/examples/<slug>/<slug>-light.html" '[["key"," "],["wait",900],["shot","'"$WORK_DIR"'/shots/exploded-light.png"]]'
node "$WORK_DIR/scripts/capture.mjs" "$WORK_DIR/examples/<slug>/<slug>.html" --out "$WORK_DIR/shots/assembled-dark.png"
node "$WORK_DIR/scripts/drive.mjs" "$WORK_DIR/examples/<slug>/<slug>.html" '[["key"," "],["wait",900],["shot","'"$WORK_DIR"'/shots/exploded-dark.png"]]'
```
Inspect the generated PNGs (`exploded-light.png`, `assembled-light.png`, `<slug>-drawing-a4.png`, `<slug>-detailed-a4.png`) to confirm zero overlapping callout pins, crisp 4-tone shading, clean explosion separation, and balanced framing before delivering.

---

## 4. Delivery Guidance (Mopheus & Interactive Sessions)

Match the deliverables to the user's intent while keeping a high craftsmanship bar (never cut corners with text-only replies or toy diagrams):

1. **Explicit User Scope Wins**:
   - If the user asks for a specific artifact (e.g., "just the interactive HTML", "only light theme", "export an A4 drawing PDF", or a targeted revision), build and attach what was asked plus a verification screenshot (`.png`) so the result is immediately visible in the comment stream.
2. **Open-Ended Showcase Requests (Default Flagship Package)**:
   - When the user gives an open-ended prompt (e.g., "draw an anatomy diagram of X") without restricting the format, go all-out and deliver the full showcase combination:
     - **Preview PNGs (`*.png`)**: Assembled and exploded views (plus A4 sheet preview if printed) so the reader sees the work inline in the ticket comment without downloading first.
     - **Interactive HTML (`*.html`)**: Standalone, zero-dependency interactive page(s).
     - **A4 Engineering Blueprint (`*.pdf`)**: Printable vector A4 drawing/explainer via `scripts/print.mjs` when an engineering sheet adds value to the showcase.

### Mopheus Ticket Submission Pattern
When replying to a Mopheus Ticket (`$MOPHEUS_TICKET_ID` or ticket ID from prompt), always attach the generated files via `--attachment` on `mopheus ticket comment add` so the user can view the PNGs inline and preview/download the HTML/PDF directly in the Mopheus Web UI:

```bash
# Attach the generated previews and deliverables that match the task scope:
mopheus ticket comment add "<ticket-id>" \
  --content-file "$WORK_DIR/comment.md" \
  --attachment "$WORK_DIR/shots/exploded-light.png" \
  --attachment "$WORK_DIR/shots/assembled-light.png" \
  --attachment "$WORK_DIR/examples/<slug>/<slug>-light.html" \
  --attachment "$WORK_DIR/examples/<slug>/<slug>-drawing-a4.pdf"
```

---

## 5. Detailed Reference Manuals

Read these bundled references when you need exact function signatures or advanced patterns:
- `references/kit.md`: Full API signatures for `iso-kit.mjs`, `lathe.mjs`, `tube.mjs`, and `audit.mjs`.
- `references/craft.md`: Mechanical parts vocabulary, tone tables, painter's order splits, pipe routing, and cutaway rules.
- `references/motion.md`: Spring physics, staggered explosion choreography, pointer/keyboard accessibility, and live readouts.
- `references/print.md`: Complete `sheet.mjs` specification for A4 `drawing`, `detailed`, and `poster` blueprints.
- `references/verify.md`: Visual inspection checklist for junctions, flanges, tubes, and callout pins.
