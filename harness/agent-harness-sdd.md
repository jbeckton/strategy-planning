# SDD-001 — Agent Harness for Copilot SDK

| Field | Value |
|---|---|
| Author | Platform Engineering |
| Status | Draft · Rev B · awaiting review |
| Last edited | 2026-05-19 |
| Runtime | Node 20 LTS · TypeScript 5.4 |
| Distribution | Bundled CLI |
| Audience | Engineering · platform tools |

---

## § 01 — Overview

*Goals, non-goals, and shape of the deliverable.*

### What we are building

A bootstrap project, not a platform. The harness is a well-structured, working starting point for Copilot SDK agent development. It wires the SDK client, mounts every hook, runs a responsive Terminal UI, and includes reference implementations of the patterns teams will need — session management, event fan-out, intent dispatch, state storage, and permission handling.

Teams fork or copy the harness and own the result. The source is theirs to modify. The value is in not starting from zero and in having the right architectural decisions already made and encoded.

### Goals

- Cover 100% of the SDK's session, messaging, hook, and event surface in the bootstrap.
- Provide a TUI that never blocks the underlying tool loop.
- Include reference implementations for all common patterns: tools, agents, skills, MCP integration, and session-scoped state storage.
- Be immediately forkable — a team should be able to clone, customise, and run their first agent turn within a day.
- Encode clear architectural boundaries as conventions, not enforcement — teams will cross them when their use case demands it.

### Non-goals

- Not a closed platform — teams are expected to modify `src/` for domain-specific agent state, control flow, and business logic.
- No remote/web hosting in v1 — local TUI only.
- No authentication beyond what the bundled CLI already provides.
- Not a reusable library in v1. Library extraction is a possible future effort once patterns stabilise across multiple forks.

### Design note: state and control flow

Custom agent state — what gets stored, how tool results feed into subsequent tool inputs, how accumulated state influences LLM prompts, and any conditional routing between tool calls — is domain-specific and belongs in the fork, not in the harness core. The harness provides a simple session-scoped file store as a reference pattern. Teams are expected to replace or extend it to fit their agent's actual state model. This is intentional: encoding a generic state machine in the harness would constrain the very use cases it is meant to accelerate.

### Capability matrix

| Capability | SDK surface | Bootstrap location |
|---|---|---|
| Session lifecycle | `createSession` · `resumeSession` · `listSessions` · `deleteSession` · `disconnect` | `src/core/session.ts` |
| Messaging modes | `send({ mode:"enqueue" })` · `send({ mode:"immediate" })` | `src/core/dispatcher.ts` |
| Event stream | `assistant.message_delta` · `tool.execution_partial_result` · `session.idle` · `permission.requested` · … | `src/core/bus.ts → tui` |
| Hooks | `onSessionStart` · `onUserPromptSubmitted` · `onPreToolUse` · `onPostToolUse` · `onSessionEnd` · `onErrorOccurred` | `src/hooks/*` |
| Custom tools | `registerTools()` | `src/tools/` · `tools/` |
| Sub-agents | `customAgents` | `agents/` |
| Skills | `skillDirectories` | `skills/` |
| External tools | `mcpServers` | `mcp/servers.json` |
| Session-scoped state | `session.workspace_path` (SDK-provided path) | `src/core/store.ts` |

---

## § 02 — Architecture

*How the TUI, the SDK client, and the filesystem talk to each other.*

Three layers. The TUI never calls the SDK directly — it sends intents through a dispatcher and renders state mutations off an internal event bus. The render loop and the SDK's tool loop run on independent timelines; neither can stall the other.

```
┌─────────────────────────────────────────────────────────┐
│  PRESENTATION · TTY                                     │
│  TUI shell (Ink / React)                                │
│  stdin → intents · state → frame                        │
│                                                         │
│  VIEW MODEL                  INPUT                      │
│  Reducer · derived state     Command parser · slash-cmds│
│  selectors per pane          /resume · /sessions · /perm│
└──────────────────┬──────────────────────────────────────┘
                   │  intents ↓ · events ↑
┌──────────────────┴──────────────────────────────────────┐
│  DISPATCH                CORE                  BUS      │
│  Intent dispatcher       Copilot SDK client    Event bus│
│  enqueue · immediate     hooks·tools·agents    fan-out  │
│                                                         │
│  STORE                                                  │
│  Session-scoped key-value (session.workspace_path)      │
│  replace or extend this for your agent's state model    │
└──────────────────┬──────────────────────────────────────┘
                   │  SDK owns conversation persistence ↕
┌──────────────────┴──────────────────────────────────────┐
│  SDK-MANAGED STORE    CONFIG · DISK       EXT           │
│  Copilot CLI session  ./harness.config.ts MCP servers   │
│  source of truth      tools·agents·skills spawned by SDK│
└─────────────────────────────────────────────────────────┘
```

### Render loop ↔ tool loop

The SDK runs its own internal turn loop. The harness treats that loop as a producer of events and a consumer of intents. The TUI is a third actor that reads a reactive view-model and writes intents; it is never on the critical path of a tool call.

### Persistence model

Conversation history and session state are owned entirely by the Copilot CLI's store. `listSessions()`, `resumeSession(id)`, and `deleteSession(id)` all delegate straight to the SDK. On resume the SDK replays its own history through `session.events()`; the TUI reducer consumes that stream identically to a live turn.

Custom agent state — anything beyond the conversation — is written to `session.workspace_path` by `src/core/store.ts`. That directory is session-scoped and survives resume. Teams replace the backing mechanism as needed.

---

## § 03 — Project layout

*Starting structure — fork and reshape as needed.*

```
harness/
├── package.json                     // bin: "harness" → dist/cli.js
├── tsconfig.json
├── harness.config.ts                // starting config — customise tools, agents, skills, mcp
│
├── src/
│   ├── cli.ts                       // entry point — parses argv, boots core, mounts TUI
│   │
│   ├── core/                        // SDK wiring and shared infrastructure
│   │   ├── client.ts                // createHarnessClient() — SDK init, hooks, tools, bus
│   │   ├── session.ts               // thin wrappers: create/resume/list/delete/disconnect
│   │   ├── dispatcher.ts            // send(intent, { mode }) — enqueue vs immediate
│   │   ├── bus.ts                   // AsyncIterable<HarnessEvent> fan-out
│   │   ├── store.ts                 // session-scoped key-value store — replace for custom state
│   │   └── types.ts                 // HarnessEvent, Intent, HarnessCtx, StoreAdapter
│   │
│   ├── hooks/                       // one file per SDK hook — wire your agent logic here
│   │   ├── onSessionStart.ts        // initialise store, inject system prompt, load context
│   │   ├── onUserPromptSubmitted.ts // redact secrets, attach files, pre-process input
│   │   ├── onPreToolUse.ts          // policy gate, arg rewriting, read/write store
│   │   ├── onPostToolUse.ts         // telemetry, write results to store, cache invalidation
│   │   ├── onSessionEnd.ts          // flush store, upload trace, cleanup
│   │   ├── onErrorOccurred.ts       // retry logic, error surfacing, alerting
│   │   └── index.ts                 // composes all hooks into the SDK config object
│   │
│   ├── tui/                         // presentation layer
│   │   ├── App.tsx                  // root Ink component
│   │   ├── panes/
│   │   │   ├── SessionList.tsx      // /sessions sidebar
│   │   │   ├── Conversation.tsx     // streamed assistant deltas
│   │   │   ├── ToolTrace.tsx        // tool execution (collapsed by default, ⌃t to expand)
│   │   │   └── PermissionPrompt.tsx // permission.requested inline collapsible
│   │   ├── commands/
│   │   │   ├── resume.ts
│   │   │   ├── sessions.ts
│   │   │   ├── steer.ts             // !... → mode:"immediate"
│   │   │   └── quit.ts
│   │   ├── reducer.ts               // pure event → view-model
│   │   └── theme.ts
│   │
│   ├── tools/                       // built-in tool examples — add yours here or in tools/
│   │   ├── registry.ts
│   │   └── fs.ts
│   │
│   └── util/
│       ├── log.ts
│       └── paths.ts                 // ~/.harness/logs, session.workspace_path helpers
│
├── tools/                           // your custom tools — registered in harness.config.ts
│   └── .gitkeep
├── agents/                          // your custom sub-agents
│   └── .gitkeep
├── skills/                          // prompt modules — *.skill.md / *.skill.ts
│   └── .gitkeep
├── mcp/                             // MCP server definitions
│   └── servers.json
│
└── ~/.harness/
    └── logs/
        └── harness.log              // diagnostic log — TUI and hook events
```

**Conventions (not enforced):** `src/core/` and `src/tui/` are separated so SDK wiring and presentation stay independent. `src/hooks/` is where most agent-specific logic will live once the harness is forked. The root-level folders (`tools/`, `agents/`, `skills/`, `mcp/`) are the lightest-touch starting points — add your domain code there first, then move logic into hooks and core as the state model becomes clearer.

---

## § 04 — Core implementation

*Boot sequence, client construction, persistence.*

### 4.1 — Client construction with the full hook lifecycle

A single factory builds the SDK client with every hook mounted, all extension surfaces wired from config, and a typed event bus the TUI subscribes to.

**`src/core/client.ts`**
```typescript
import { createCopilotClient } from "@github/copilot-sdk";
import { loadConfig }         from "./config";
import { Bus }                from "./bus";
import { Store }              from "./store";
import * as hooks             from "../hooks";
import { builtInTools }       from "../tools/registry";

export async function createHarnessClient(opts: { sessionId?: string }) {
  const cfg = await loadConfig();
  const bus = new Bus();

  const client = await createCopilotClient({
    customAgents:     cfg.agents,
    skillDirectories: cfg.skillDirs,
    mcpServers:       cfg.mcpServers,
    hooks: {
      onSessionStart:        hooks.onSessionStart(bus),
      onUserPromptSubmitted: hooks.onUserPromptSubmitted(bus),
      onPreToolUse:          hooks.onPreToolUse(bus),
      onPostToolUse:         hooks.onPostToolUse(bus),
      onSessionEnd:          hooks.onSessionEnd(bus),
      onErrorOccurred:       hooks.onErrorOccurred(bus),
    },
  });

  await client.registerTools([...builtInTools(), ...cfg.tools]);

  const session = opts.sessionId
    ? await client.resumeSession(opts.sessionId)
    : await client.createSession({ workingDir: process.cwd() });

  // Store is initialised against the SDK's session workspace path.
  // Replace Store with your own implementation for custom state models.
  const store = new Store(session.workspace_path);

  (async () => {
    for await (const ev of session.events()) {
      bus.emit(ev);
      if (ev.type === "session.idle")         bus.emit({ type: "harness.idle" });
      if (ev.type === "permission.requested") bus.emit({ type: "harness.permission", ev });
    }
  })();

  return { client, session, bus, store };
}
```

### 4.2 — Sessions: thin wrappers around the SDK's store

**`src/core/session.ts`**
```typescript
import type { CopilotClient, Session } from "@github/copilot-sdk";

export const sessions = (client: CopilotClient) => ({
  list:       () =>             client.listSessions(),
  resume:     (id: string) =>  client.resumeSession(id),
  create:     () =>             client.createSession({ workingDir: process.cwd() }),
  remove:     (id: string) =>  client.deleteSession(id),
  disconnect: (s: Session) => client.disconnect(s),
});
```

### 4.3 — Messaging: enqueue vs. immediate

**`src/core/dispatcher.ts`**
```typescript
export type Intent =
  | { kind: "user.message";     text: string;    mode: "enqueue" | "immediate" }
  | { kind: "permission.reply"; grantId: string; decision: "allow" | "deny" }
  | { kind: "interrupt" };

export function dispatcher(ctx: HarnessCtx) {
  return async (i: Intent) => {
    switch (i.kind) {
      case "user.message":
        return ctx.session.send({ role: "user", content: i.text, mode: i.mode });
      case "permission.reply":
        return ctx.session.resolvePermission(i.grantId, i.decision);
      case "interrupt":
        return ctx.session.interrupt();
    }
  };
}
```

### 4.4 — Session-scoped state store

The store provides a simple key-value interface backed by the SDK's `session.workspace_path`. It persists across tool calls within a session and survives resume. This is a reference implementation — replace the backing mechanism, extend the interface, or swap it for a database-backed store once your agent's state model is defined.

**`src/core/store.ts`**
```typescript
import { readFile, writeFile } from "fs/promises";
import { join } from "path";

export class Store {
  private path: string;
  private data: Record<string, unknown> = {};

  constructor(workspacePath: string) {
    this.path = join(workspacePath, "harness-state.json");
  }

  async load(): Promise<void> {
    try {
      const raw = await readFile(this.path, "utf-8");
      this.data = JSON.parse(raw);
    } catch {
      this.data = {};   // first run — no state file yet
    }
  }

  async flush(): Promise<void> {
    await writeFile(this.path, JSON.stringify(this.data, null, 2));
  }

  get<T>(key: string): T | undefined {
    return this.data[key] as T;
  }

  async set<T>(key: string, value: T): Promise<void> {
    this.data[key] = value;
    await this.flush();
  }

  async delete(key: string): Promise<void> {
    delete this.data[key];
    await this.flush();
  }
}
```

**Usage in hooks:** hooks receive the store through `HarnessCtx` and can read or write arbitrary state. The schema is entirely up to the fork — the store doesn't know or care what's in it.

```typescript
// src/hooks/onPostToolUse.ts — write tool result to store for use in later turns
export const onPostToolUse = (bus: Bus) =>
  async (ctx: PostToolUseCtx & { store: Store }) => {
    bus.emit({ type: "tui.tool.end", tool: ctx.toolName, duration: ctx.duration });

    // Store result keyed by tool name — subsequent tools or prompts can read this.
    // Extend this pattern to build up structured agent state across a multi-step workflow.
    await ctx.store.set(`result:${ctx.toolName}`, ctx.result);
  };
```

### 4.5 — Hook scaffold

**`src/hooks/onPreToolUse.ts`** (representative example)
```typescript
import type { Bus } from "../core/bus";
import type { Store } from "../core/store";

export const onPreToolUse = (bus: Bus) =>
  async (ctx: PreToolUseCtx & { store: Store }) => {
    bus.emit({ type: "tui.tool.start", tool: ctx.toolName, args: ctx.args });

    // Read store state to inform policy decisions, arg rewriting, or context injection.
    // This is where domain-specific pre-tool logic lives once the harness is forked.

    return { action: "continue" } as const;
  };
```

---

## § 05 — TUI event loop

*A responsive interface that never blocks the tool loop.*

### Swimlane timeline

| t | User · TUI (render timeline) | Harness core · bus | SDK · tool loop (worker timeline) |
|---|---|---|---|
| t₀ | User types `refactor login.ts` + ⏎ | `dispatcher.send({mode:"enqueue"})` | `session.events()` begins yielding |
| t₁ | Stream paints; renders `assistant.message_delta` | bus fans out to all subscribers | `assistant.message_delta` ×N |
| t₂ | Tool trace lights up; `onPreToolUse` reads store | `bus.emit(tui.tool.start)` | `tool.execution_partial_result` |
| t₃ | Permission prompt inline; `y / n / ?` to expand | `dispatcher` → `resolvePermission()` | `permission.requested` |
| t₄ | User types `!use OAuth2 instead` | `dispatcher.send({mode:"immediate"})` | turn re-plans mid-flight |
| t₅ | Status: idle; `onPostToolUse` writes result to store | `bus.emit("harness.idle")` | `session.idle` |

### Why this stays responsive

- **Single async iterator, fan-out.** The bus is the only consumer of `session.events()`. Subscribers get buffered slices — a slow subscriber cannot back-pressure the SDK.
- **Pure reducer.** The TUI view-model is synchronously rebuilt on every event. No `await` in the render path.
- **Immediate-mode steering.** Leading `!` converts input to `mode:"immediate"` — redirect an in-flight turn without waiting for idle.
- **Permission prompts are non-blocking.** `permission.requested` drops a collapsible row into the trace pane; the stream keeps rendering.

### Streamed events reference

| Event | TUI reaction |
|---|---|
| `assistant.message_delta` | Append chunk to message bubble; auto-scroll if at bottom. |
| `tool.execution_started` | Push a row into the Tool Trace pane. |
| `tool.execution_partial_result` | Stream stdout/stderr into that row. |
| `tool.execution_completed` | Mark row ✓ or ✗ with exit summary. |
| `permission.requested` | Collapsible inline prompt in trace row; input pane stays usable. |
| `session.idle` | Status line flips green; turn complete. |
| `session.error` | Surface via `onErrorOccurred` → toast pane. |

### 5.1 — TUI mock (illustrative)

```
harness · session 2026-05-18_a4f2c1
mode: enqueue · idle: false · ⏎ send · ! steer · ⌃t trace · /help
┌─────────────────┬──────────────────────────────────────────────────┐
│ Sessions        │ Conversation                                      │
│                 │                                                   │
│ ▸ a4f2c1 14:02  │ › refactor login.ts to use OAuth2                 │
│   b81e9d yester │ ‹ Reading login.ts… (124 lines)                   │
│   3f0a17 2d ago │ ⚙ tool read_file(path="login.ts") ✓ 12ms          │
│   9c2d05 last wk│ ⚙ tool grep(pattern="passwordLogin") ✓ 3 hits     │
│   5e7b91 last wk│ ▸ permission write_file login.ts [ y · n · ? ]    │
│                 │     diff preview · 42 lines · auto-allow? n        │
│                 │ ‹ I'll replace the credential flow with OAuth2▍    │
│                 ├──────────────────────────────────────────────────┤
│                 │ Tool trace · 5 · ⌃t (collapsed)                   │
└─────────────────┴──────────────────────────────────────────────────┘
❯ !use OAuth2 authorization-code, not implicit flow▍
```

---

## § 06 — Hook reference

| Hook | Fires | Bootstrap behaviour | Typical fork customisation |
|---|---|---|---|
| `onSessionStart` | Once, after `createSession` or `resumeSession`. | Loads store; emits `tui.session.opened`. | Inject system prompt; load org context; initialise agent state. |
| `onUserPromptSubmitted` | After dispatcher sends user message; before turn begins. | Emits `tui.user.message`. | Secret-redaction; attach files by `@path`; pre-process input. |
| `onPreToolUse` | Before every tool invocation. | Emits `tui.tool.start`; reads store for context. | Policy gate; arg rewriting; inject prior tool results into args. |
| `onPostToolUse` | After every tool invocation, success or failure. | Emits `tui.tool.end`; writes result to store. | Structured state accumulation; telemetry; cache invalidation. |
| `onSessionEnd` | On graceful disconnect or exit. | Flushes store; emits `tui.session.closed`. | Upload trace; persist state to external store; cleanup. |
| `onErrorOccurred` | On any SDK-surfaced error. | Emits `tui.toast.error`; logs to `~/.harness/logs/`. | Retry logic; alerting; structured error capture. |

---

## § 07 — Customisation starting points

*What teams typically change first after forking.*

The harness is a starting point. There is no platform boundary preventing modification of any file. These are the areas teams reach first:

| What to customise | Where | Notes |
|---|---|---|
| Agent tools | `tools/` + `harness.config.ts` | Register via `cfg.tools`; the tool receives `ctx.store` for state access |
| Hook logic | `src/hooks/*.ts` | Each hook is a standalone file — replace the body, keep the signature |
| State model | `src/core/store.ts` | Replace the JSON file store with SQLite, a remote DB, or any async interface |
| System prompt / skills | `skills/` | Markdown or TS skill files; loaded by SDK per turn |
| Sub-agents | `agents/` + `harness.config.ts` | Each agent gets its own system prompt and tool restrictions |
| MCP servers | `mcp/servers.json` | Add any MCP-compatible external tool server |
| TUI layout | `src/tui/panes/` | Add panes, change layout, or replace Ink entirely for headless use |
| Session state routing | `src/hooks/onPreToolUse.ts` | Read accumulated store state; shape tool args; inject into LLM context via skills |

---

## § 08 — Next steps

### Decisions recorded

| Question | Resolution |
|---|---|
| Platform vs. bootstrap | Bootstrap. Teams fork and own. Source modification is expected and supported. |
| Session store ownership | SDK owns conversation history. Harness `Store` covers custom agent state only. |
| State model | Reference JSON file store in `src/core/store.ts`. Teams replace for their use case. |
| Permission UX | Inline collapsible in trace pane. `y / n / ?`; `?` expands to show args + diff. |
| Replay log | None. Diagnostic `harness.log` only — daily-rotated, never replayed. |
| Programmatic API | No. CLI only in v1. Library extraction is a future effort once fork patterns stabilise. |

### Proposed milestones

| Milestone | Scope | Est. |
|---|---|---|
| M1 — Skeleton | Directory structure, SDK client factory, store, no-op hooks, plain stdout TUI | 1 week |
| M2 — Streaming TUI | Ink panes, reducer, slash-commands, permission prompt; **leadership checkpoint demo** | 1 week |
| M3 — Session UX | `--resume <id>`, `/sessions` picker, `/delete` | 2 days |
| M4 — Extension loaders | Autoload `tools/`, `agents/`, `skills/`, `mcp/`; store wired into hook context | 1 week |
| M5 — Polish & handoff | Diagnostic logging, telemetry in `onPostToolUse`, end-to-end demo, fork guide | 1 week |

---

*SDD-001 · Rev B · Draft — Platform Engineering · 2026*
