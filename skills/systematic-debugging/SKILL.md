---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Six Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Build a Feedback Loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic, runnable pass/fail signal for the bug, you will find the cause. If you don't have one, no amount of staring at code will save you.

**Be aggressive. Be creative. Refuse to give up.** Spend disproportionate effort here.

#### Ways to construct one — try in roughly this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e
2. **Curl / HTTP script** against a running dev server
3. **CLI invocation** with fixture input, diff stdout against known-good snapshot
4. **Headless browser script** (Playwright / Puppeteer) — drives UI, asserts on DOM/console/network
5. **Replay a captured trace** — save a real network request/payload to disk; replay in isolation
6. **Throwaway harness** — spin up minimal subset of the system (one service, mocked deps) that exercises the bug code path
7. **Property / fuzz loop** — if bug is "sometimes wrong output", run 1000 random inputs and look for failure mode
8. **Bisection harness** — if bug appeared between two known states (commit/dataset/version), automate "boot at state X, check, repeat" so you can `git bisect run`
9. **Differential loop** — run same input through old-version vs new-version (or two configs), diff outputs
10. **HITL bash script** — last resort. If a human must click, drive them with a structured loop so the captured output still feeds back to you

#### Iterate on the loop itself

Treat the loop as a product. Once you have _a_ loop, ask:
- Can I make it faster? (Cache setup, skip unrelated init, narrow scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

A 30-second flaky loop is barely better than no loop. A 2-second deterministic loop is a debugging superpower.

#### Non-deterministic (flaky) bugs

The goal is not perfect reproduction but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate until it is.

#### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to whatever environment reproduces it, (b) a captured artifact (HAR file, log dump, core dump, screen recording), or (c) permission to add temporary production instrumentation. **Do not proceed to Phase 2 without a loop.**

---

### Phase 1b: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce via the Loop**
   - Run your feedback loop. Watch the bug appear.
   - Confirm the loop produces the failure mode the **user** described — not a different nearby failure. Wrong bug = wrong fix.
   - Capture the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix addresses it.

3. **Gather Evidence in Multi-Component Systems**

   **WHEN system has multiple components (CI → build → signing, API → service → database):**

   **BEFORE proposing fixes, add diagnostic instrumentation:**
   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once to gather evidence showing WHERE it breaks
   THEN analyze evidence to identify failing component
   THEN investigate that specific component
   ```

   **Example (multi-layer system):**
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   **This reveals:** Which layer fails (secrets → workflow ✓, workflow → build ✗)

4. **Trace Data Flow**

   **WHEN error is deep in call stack:**

   See `root-cause-tracing.md` in this directory for the complete backward tracing technique.

   **Quick version:**
   - Where does bad value originate?
   - What called this with bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate similar working code in same codebase
   - What works that's similar to what's broken?

2. **Compare Against References**
   - If implementing pattern, read reference implementation COMPLETELY
   - Don't skim - read every line
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components does this need?
   - What settings, config, environment?
   - What assumptions does it make?

### Phase 3: Generate and Rank Hypotheses

**Scientific method — but generate multiple hypotheses before testing any:**

1. **Generate 3–5 Ranked Hypotheses**
   - Single-hypothesis generation anchors on the first plausible idea — resist this
   - Each hypothesis must be **falsifiable**: state the prediction it makes
   - Format: "If [X] is the cause, then [Y] will happen / [Y] will disappear"
   - If you cannot state the prediction, the hypothesis is a vibe — discard or sharpen it
   - Rank by probability given all evidence seen so far

2. **Show the Ranked List to the User**
   - They often have domain knowledge that instantly re-ranks ("we just deployed a change to #3")
   - Cheap checkpoint, big time saver
   - Proceed with your ranking if the user is AFK

3. **Test Hypotheses via Instrumentation**
   - Each probe must map to a specific prediction from Step 1
   - **Change one variable at a time**
   - Tool preference order: (1) debugger/REPL — one breakpoint beats ten logs; (2) targeted logs at the boundaries that distinguish hypotheses; (3) never "log everything and grep"
   - **Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end is a single grep. Tagged logs die; untagged logs survive.
   - For performance regressions: measure first with `performance.now()` / profiler / query plan, then bisect. Logs are usually wrong for perf.

4. **Verify Before Continuing**
   - Did it work? Yes → Phase 4
   - Didn't work? Return to Step 1 with new information, re-rank hypotheses
   - DON'T add more fixes on top without going back through the ranked list

5. **When You Don't Know**
   - Say "I don't understand X"
   - Don't pretend to know
   - Ask for help
   - Research more

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Create Failing Test Case**
   - Simplest possible reproduction
   - **Seam must be correct** — test exercises the real bug pattern as it occurs at the call site. A shallow seam (single-caller test when bug needs multiple callers) gives false confidence. If no correct seam exists, that itself is a finding — document it.
   - Automated test if possible; one-off script if no framework
   - MUST have before fixing
   - Use the `superpowers:test-driven-development` skill for writing proper failing tests

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring

3. **Verify Fix**
   - Test passes now?
   - No other tests broken?
   - Issue actually resolved?
   - Re-run Phase 1 feedback loop against the original (unminimised) scenario

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If ≥ 3: STOP and question the architecture (Phase 5)**
   - DON'T attempt Fix #4 without architectural discussion

### Phase 5: Question Architecture

**Pattern indicating architectural problem:**
- Each fix reveals new shared state/coupling/problem in different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor architecture vs. continue fixing symptoms?

**Discuss with your human partner before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

### Phase 6: Cleanup + Post-Mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix — tagged logs die)
- [ ] Throwaway prototypes deleted (or moved to a clearly-marked debug location)
- [ ] **The hypothesis that turned out correct is stated in the commit / PR message** — so the next debugger learns

**Then ask: what would have prevented this bug?** If the answer involves architectural change (no good test seam, tangled callers, hidden coupling), consider running `/improve-codebase-architecture` after the fix is in. Make the recommendation after the fix, not before — you have more information now than when you started.

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals new problem in different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (see Phase 5)

## your human partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- "Is that not happening?" - You assumed without verifying
- "Will it show us...?" - You should have added evidence gathering
- "Stop guessing" - You're proposing fixes without understanding
- "Ultrathink this" - Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) - Your approach isn't working

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|-----------------|
| **1. Feedback Loop** | Build fast deterministic repro loop; iterate on it | Loop runs reliably, bug visible in seconds |
| **1b. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypotheses** | Generate 3–5 ranked, falsifiable; show to user; instrument | Confirmed or new hypothesis |
| **4. Implementation** | Create test at correct seam, fix, verify | Bug resolved, tests pass |
| **5. Architecture** | Question fundamentals if 3+ fixes failed | Architectural decision |
| **6. Cleanup** | Remove debug tags, delete throwaways, write commit message | Clean, documented |

## When Process Reveals "No Root Cause"

If systematic investigation reveals issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated
3. Implement appropriate handling (retry, timeout, error message)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

## Supporting Techniques

These techniques are part of systematic debugging and available in this directory:

- **`root-cause-tracing.md`** - Trace bugs backward through call stack to find original trigger
- **`defense-in-depth.md`** - Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** - Replace arbitrary timeouts with condition polling

**Related skills:**
- **superpowers:test-driven-development** - For creating failing test case at the correct seam (Phase 4, Step 1)
- **superpowers:verification-before-completion** - Verify fix worked before claiming success

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common
