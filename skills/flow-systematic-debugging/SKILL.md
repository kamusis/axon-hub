---
name: flow-systematic-debugging
description: Systematic debugging workflow with enforced phases. Use when encountering bugs, test failures, or unexpected behavior. Guides through root cause investigation → pattern analysis → hypothesis testing → implementation, with mandatory checkpoints.
type: flow
---

# Flow: Systematic Debugging

**Core Principle:** ALWAYS find root cause before attempting fixes. NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

This flow skill enforces the four-phase debugging methodology through structured execution.

## Flow Diagram

```mermaid
flowchart TD
    A([BEGIN<br/>Received debugging request]) --> B[Phase 1.1: Read and analyze error messages<br/>Carefully read all errors, warnings, stack traces]
    
    B --> C{Contains<br/>clear solution?}
    C -->|Yes| D[Record root cause<br/>Go directly to Phase 2]
    C -->|No| E[Phase 1.2: Reproduce issue<br/>Confirm can be consistently triggered]
    
    E --> F{Can reproduce?}
    F -->|No| G[Collect more data<br/>Add logs/diagnostics]
    G --> E
    F -->|Yes| H[Phase 1.3: Check recent changes<br/>git diff / recent commits / dependency changes]
    
    H --> I{Is it a<br/>multi-component system?}
    I -->|Yes| J[Phase 1.4: Add component boundary diagnostics<br/>Input/output/environment for each layer]
    J --> K[Run and analyze<br/>Identify faulty component]
    I -->|No| L[Phase 1.5: Trace data flow<br/>Backtrace to error source]
    
    K --> L
    L --> M{Root cause identified?}
    M -->|No| B
    M -->|Yes| D
    D --> N[Phase 2: Pattern analysis<br/>Find working examples/compare differences/understand dependencies]
    
    N --> O[Phase 3: Form hypothesis<br/>"X is the root cause because Y"]
    O --> P[Phase 3.5: Minimal test<br/>Single variable verification]
    
    P --> Q{Test passed?}
    Q -->|No| R[Form new hypothesis<br/>Record failure reason]
    R --> B
    Q -->|Yes| S[Phase 4: Implement fix]
    
    S --> T[4.1: Create failing test case<br/>Must be automated]
    T --> U[4.2: Implement single fix<br/>Only change root cause]
    U --> V[4.3: Verify fix<br/>Tests pass? No side effects?]
    
    V --> W{Fix successful?}
    W -->|Yes| X([END Success<br/>Fix verified])
    W -->|No| Y{Fix attempts made}
    
    Y -->|< 3| Z[Return to Phase 1<br/>Re-analyze with new information]
    Z --> B
    Y -->|≥ 3| AA[STOP: Question architecture<br/>Discuss refactoring with user]
    AA --> AB([END Needs architectural discussion])
```

## Phase Details

### Phase 1: Root Cause Investigation

**Iron Law:** Do NOT propose any fix before completing Phase 1.

**Steps:**
1. **Read Error Messages Carefully** - Read line by line, don't skip any warnings
2. **Reproduce Consistently** - Record exact reproduction steps
3. **Check Recent Changes** - git log, git diff, dependency changes
4. **Gather Multi-Component Evidence** (if applicable)
5. **Trace Data Flow** - Backtrace to error source

**Red Flags (STOP and return to Phase 1):**
- "Quick fix for now, investigate later"
- "Probably X, let me fix that"
- "I'll adapt the pattern differently"
- Skipping error messages

### Phase 2: Pattern Analysis

**Must complete:**
- Find working examples in same codebase
- Read reference implementation completely
- List every difference (don't assume "that can't matter")
- Understand all dependencies

### Phase 3: Hypothesis and Testing

**Scientific method enforced:**
- State hypothesis clearly: "I think X is the root cause because Y"
- Make SMALLEST possible change to test
- One variable at a time
- If fails: form NEW hypothesis, return to Phase 1

### Phase 4: Implementation

**Required sequence:**
1. Create failing test case first (use test-driven-development skill)
2. Implement SINGLE fix (no "while I'm here")
3. Verify fix (tests pass, no new issues)

**Failure handling:**
- Success → END
- Failure, < 3 attempts → Return to Phase 1 with new info
- Failure, ≥ 3 attempts → STOP, question architecture

## Phase Transition Rules

| From | To | Condition |
|------|-----|-----------|
| Phase 1 | Phase 2 | Root cause identified and documented |
| Phase 2 | Phase 3 | Pattern differences understood |
| Phase 3 | Phase 4 | Hypothesis confirmed by minimal test |
| Phase 3 | Phase 1 | Hypothesis rejected, new data gathered |
| Phase 4 | END | Fix verified, tests pass |
| Phase 4 | Phase 1 | Fix failed, attempts < 3 |
| Phase 4 | END (arch) | Fix failed, attempts ≥ 3 |

## Self-Check Questions

At each phase transition, answer:

**Before Phase 2:**
- [ ] Can I explain exactly WHY this bug happens?
- [ ] Do I know the commit/change that introduced it?
- [ ] Have I traced to the source, not just the symptom?

**Before Phase 3:**
- [ ] What works that's similar to what's broken?
- [ ] What's different between working and broken?
- [ ] Did I read the reference implementation completely?

**Before Phase 4:**
- [ ] Can I state "X is the cause because Y"?
- [ ] Did I test the hypothesis with a minimal change?
- [ ] Is the hypothesis confirmed?

**Before END:**
- [ ] Do I have a failing test case?
- [ ] Did I make only ONE change?
- [ ] Do all tests pass?
- [ ] Is the original issue resolved?

## Common Rationalizations (REJECT THESE)

| Excuse | Response |
|--------|----------|
| "Issue is simple" | Simple issues have root causes too. Process is fast. |
| "Emergency, no time" | Systematic debugging is FASTER than guess-and-check. |
| "Just try this first" | First fix sets bad pattern. Do it right from start. |
| "Test after confirming fix" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes saves time" | Can't isolate what worked. Causes new bugs. |
| "One more fix attempt" | 3+ failures = architectural problem. Question pattern. |

## Real-World Impact

- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

## When to Use This Flow

**Always for:**
- Test failures
- Production bugs
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Especially when:**
- Under time pressure
- "Quick fix" seems obvious
- Already tried multiple fixes
- Previous fix didn't work
- Don't fully understand the issue

## Related Skills

- `/skill:test-driven-development` - For Phase 4 test creation
- `/skill:verification-before-completion` - For fix verification
- `/skill:systematic-debugging` - Original knowledge-base version (reference)
