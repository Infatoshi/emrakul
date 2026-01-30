# Emrakul

Agent orchestration framework. Claude is the orchestrator - specialized workers handle execution.

## Concept

- Claude handles architecture, planning, and verification
- Workers handle implementation: Codex (debugging), Gemini (tests/docs), Kimi (research), Cursor (multi-file), OpenCode (general)
- All workers run in yolo mode - no approval prompts
- Two modes: ad-hoc (single worker, synchronous) and pool (batch parallel via AlphaHENG)

## MCP Tools Available

When working in this directory, these tools are exposed via MCP:

- `delegate_codex(task, context_files, working_dir)` - deep debugging, recursive tracing
- `delegate_gemini(task, context_files, working_dir)` - tests, docs, frontend, perf
- `delegate_kimi(task)` - internet research, finding documentation
- `delegate_cursor(task, context_files, working_dir)` - complex multi-file tasks ($20k credits)
- `delegate_opencode(task, context_files, working_dir)` - general implementation, quick fixes
- `pool_submit(tasks_yaml_path)` - batch submission to AlphaHENG
- `pool_status()` - check AlphaHENG queue

## When to Delegate

Use ad-hoc delegation when:
- You need research before planning (delegate_kimi)
- A test is failing and you need deep tracing (delegate_codex)
- You need comprehensive tests written (delegate_gemini)
- Complex multi-file refactors (delegate_cursor)
- A straightforward implementation is needed (delegate_opencode)

Use pool submission when:
- Work is parallelizable with oracle verification
- Porting many similar functions
- High-variance tasks benefit from multiple attempts

## Worker Selection

- Codex: "trace why X diverges", "debug the call stack for Y", "find the root cause of Z"
- Gemini: "write tests for X", "document Y", "optimize performance of Z", "implement frontend for W"
- Kimi: "research how X works", "find documentation for Y", "what does Z do internally"
- Cursor: "refactor the entire module", "implement feature across these 10 files", complex multi-step
- OpenCode: "implement X", "fix bug in Y", "port Z to new format"

## CLI Yolo Modes

All CLIs run without approval prompts:
- Codex: `codex exec` with disk permissions
- Gemini: `--yolo` flag
- Kimi: `--print` (implicitly yolo)
- Cursor: `--print --force` flags
- OpenCode: default permissive mode

## Commands

```bash
uv sync                                      # install deps
uv run emrakul delegate codex "task"         # manual delegation
uv run emrakul delegate cursor "big task"    # use cursor credits
uv run emrakul serve                         # run MCP server
```

## Available CLIs on this machine

- codex: /opt/homebrew/bin/codex
- gemini: /opt/homebrew/bin/gemini
- cursor: /opt/homebrew/bin/cursor
- kimi: not installed
- opencode: not installed

## Style

No tables. No ASCII art. Dense text, bullet points. Token-efficient.
