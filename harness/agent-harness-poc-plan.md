# Agent Harness for Copilot SDK — Proof of Concept Plan

| Field | Value |
|---|---|
| Document type | POC Plan |
| Related doc | SDD-001 Rev B · Agent Harness for Copilot SDK |
| Status | Draft · Rev B · for engineering leadership review |
| Author | Platform Engineering |
| Date | 2026-05-19 |

---

## § 01 — POC Objectives

This proof of concept validates a single core hypothesis:

> **A well-structured Copilot SDK bootstrap — wiring, TUI, session management, hooks, and a reference state store — reduces the time from zero to a running custom agent from weeks to less than a day.**

Four concrete questions drive the POC:

1. Does the Copilot SDK's hook and event model give teams enough control to build observable, policy-aware agents without fighting the framework?
2. Does session persistence across CLI restarts meaningfully reduce developer iteration time on multi-step agent workflows?
3. Does the hook-plus-store pattern give teams a clear, practical starting point for custom agent state — even knowing they will replace or extend it?
4. Is the bootstrap structured well enough that a second engineer can fork it and reach a working first agent turn within a day?

---

## § 02 — Scope

### In scope

- Full implementation through the five milestones defined in SDD-001 §08.
- A working TUI demonstrating real-time streaming, session persistence, and inline permission handling.
- `src/core/store.ts` — reference session-scoped state store wired into hook context.
- One end-to-end validation scenario: multi-step agent task (read → analyse → guarded write) with tool results written to the store and session resume across restarts.
- A fork guide documenting the first customisation steps: adding a tool, modifying a hook, and replacing the state store.
- An M2 checkpoint demo for engineering leadership before continuing to M3–M5.

### Out of scope

- Production hardening, SLA definitions, or load testing.
- Remote/web hosting — local developer environment only.
- A reusable library or npm package (possible future effort once fork patterns stabilise).
- Any domain-specific agent logic — the harness ships with no business behaviour.

---

## § 03 — Technical approach

*Summarised from SDD-001 Rev B. Full detail, code, and diagrams live there.*

The bootstrap is three layers:

| Layer | Responsibility | Key technology |
|---|---|---|
| **Presentation** | Renders streamed events; accepts user input | Ink (React for TTY) |
| **Core** | SDK client factory, event bus, intent dispatcher, session wrappers, state store | TypeScript · `@github/copilot-sdk` |
| **Extension starting points** | `tools/`, `agents/`, `skills/`, `mcp/` — team-owned from day one | Registered via `harness.config.ts` |

**TUI / tool loop decoupling:** The render loop and the SDK's tool loop run on independent async timelines, coupled only through an event bus and a typed intent dispatcher. A blocked render or pending permission prompt cannot stall an in-flight agent turn.

**Session ownership:** Conversation history is owned entirely by the Copilot CLI's store. Custom agent state — tool results, workflow progress, accumulated context — is written by the harness `Store` to the SDK-provided `session.workspace_path`. This survives resume. Teams replace the store implementation for their use case; the interface remains the same.

**Bootstrap, not platform:** Teams fork the harness and own the source. The `src/hooks/` files are the primary customisation surface — that is where agent-specific state logic, tool result routing, and LLM context injection live once a team has shaped the bootstrap to their use case.

---

## § 04 — Value to future internal agent development

### 4.1 — Eliminate the bootstrapping phase entirely

Every internal agent project currently starts the same way: wire a model client, build a turn loop, add streaming, implement session persistence, figure out tool invocation, add logging, build a permission model. That work is undifferentiated — it produces inconsistent implementations and is never shared.

The bootstrap does all of it once. A team clones the harness, reads the fork guide, adds their first tool, and has a running agent turn on day one. The plumbing decisions have already been made and are already working.

**Target saving: 1–2 weeks per new agent project before any domain work begins.**

### 4.2 — Encode the right patterns, not just working code

The value of a bootstrap over a raw example is that architectural decisions are already made: the bus/dispatcher split, the hook-per-file structure, the store-in-context pattern, the session delegation model. Teams inherit those decisions with reasons attached (the SDD), not just code to copy.

When a team's agent state model diverges from the reference store — as it will — they have a clear extension point (`src/core/store.ts`), a clear wiring location (`createHarnessClient`), and a clear consumption pattern (hook context). They know what to replace and why.

### 4.3 — Consistent observability as a starting point

Every tool invocation passes through `onPreToolUse` and `onPostToolUse` from the first run. Structured hook events — tool name, args, duration, exit summary — are emitted to the bus unconditionally. Teams can add telemetry, tracing, and logging by extending those hooks rather than retrofitting instrumentation after the fact.

### 4.4 — Reduced agent iteration cost

**Session persistence** means a developer debugging step six of a multi-step workflow does not re-send five turns of context on every restart. `--resume <id>` restores the full session including any state written to the store.

**Store continuity** means tool results from turn N are available to hooks in turn N+1 without re-running the tool. This is the starting point for multi-step agent state — teams extend the schema as their workflow demands.

**Immediate-mode steering** (`!` prefix) lets the developer redirect an in-flight turn without killing the session. These are structural capabilities — teams get them from the bootstrap and do not rebuild them.

### 4.5 — A credible foundation for a future framework

The POC is explicitly a bootstrap, not a framework. But if multiple teams fork it and solve similar problems (state routing, multi-agent coordination, structured output pipelines), the patterns that emerge across those forks are the raw material for a shared framework later. Starting from a well-designed common base makes that extraction tractable. Starting from five independently-written ad-hoc implementations does not.

---

## § 05 — Success criteria

| Criterion | Verification method |
|---|---|
| All six hooks fire and emit typed bus events | Diagnostic log shows hook events for a complete agent turn |
| Tool result written to store in `onPostToolUse` | State file visible in `session.workspace_path` after a tool call |
| Store value readable in subsequent hook call | `onPreToolUse` reads prior result; logged via bus event |
| Session and store persist across CLI restarts | `--resume <id>` restores both conversation state and store contents |
| Tool trace streams partial results in real time | Live demo: partial stdout visible before tool completion |
| Permission prompt is inline and non-blocking | Agent stream continues while user reads collapsed prompt |
| Immediate-mode steering re-plans a live turn | `!`-prefixed input redirects active turn without session reset |
| Second engineer forks and reaches first agent turn | Fork guide walkthrough: timed, observed, target < 1 day |

---

## § 06 — Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| SDK API surface deviates from the SDD | Medium | High | Spike the actual SDK package before M1; update SDD §04 before writing implementation code |
| Reference store interface is too narrow for real agent state models | Medium | Medium | Keep the interface minimal (get/set/delete); document the extension points clearly in the fork guide |
| Copilot CLI session store is opaque or unstable | Medium | Medium | All session access goes through `src/core/session.ts`; SDK never called directly from hooks or TUI |
| Teams modify hooks incorrectly and break bus event flow | Low | Medium | Hook signatures are typed; bus events are typed; M5 includes a fork guide with worked examples |

---

## § 07 — Milestones and timeline

| Milestone | Deliverable | Estimate |
|---|---|---|
| **M1 — Skeleton** | Directory structure, SDK client factory, `Store`, all six hooks wired (no-op), plain stdout TUI | 1 week |
| **M2 — Streaming TUI** | Ink panes, reducer, slash-commands, permission prompt; store in hook context; **leadership checkpoint demo** | 1 week |
| **M3 — Session UX** | `--resume <id>`, `/sessions` picker, `/delete`; store verified to survive resume | 2 days |
| **M4 — Extension loaders** | Autoload `tools/`, `agents/`, `skills/`, `mcp/`; end-to-end store read/write scenario | 1 week |
| **M5 — Polish & handoff** | Diagnostic logging, telemetry in `onPostToolUse`, end-to-end demo scenario, fork guide | 1 week |
| **Total** | | **~4.5 weeks** |

M2 is the natural leadership checkpoint. The architecture is demonstrable, the store pattern is wired, and the fork walkthrough can be run. The decision to continue to M3–M5 should be confirmed at that point.

---

## § 08 — Resource requirements

| Resource | Detail |
|---|---|
| Engineering | 1 engineer (solo), full POC duration |
| GitHub Copilot access | Bundled CLI mode — existing team licence |
| Infrastructure | Local development machine only; no cloud resources required |
| Peer review | ~1 day from one additional engineer at M2 for the fork walkthrough validation |

---

## § 09 — Recommendation

Proceed. The investment is bounded — one engineer, approximately 4.5 weeks, no infrastructure spend. The M2 checkpoint is a natural gate before the bulk of the work.

The case is straightforward: every internal agent project currently rebuilds the same foundation. The bootstrap eliminates that phase permanently. The first team to use it recovers the investment; every subsequent team compounds it.

The bootstrap is not a platform commitment. Teams own their fork. There is no shared runtime to maintain, no upgrade path to manage, no abstraction to fight when the agent's state model demands something the harness didn't anticipate. That is the right tradeoff at this stage.

---

*Agent Harness POC Plan · Rev B · Draft · Platform Engineering · 2026*
