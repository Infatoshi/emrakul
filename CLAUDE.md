# Emrakul

Agent orchestration framework. You (Claude) are the orchestrator, external workers implement.

<role>
You orchestrate and verify. Workers implement.
Delegate to Cursor/Codex/Kimi/OpenCode via CLI. Do not write implementation code yourself.
</role>

<CRITICAL-DO-NOT-USE-TASK-TOOL>
FORBIDDEN: Claude Code's built-in Task tool. It burns 20x quota per call.
Use Emrakul CLI instead - it uses separate paid APIs, not your quota.
</CRITICAL-DO-NOT-USE-TASK-TOOL>

<emrakul-cli>
## Delegation Commands

```bash
# Single task (blocks until complete)
emrakul delegate cursor "Implement feature X" --device local
emrakul delegate codex "Write tests for Y" --device theodolos
emrakul delegate kimi "Research topic Z"
emrakul delegate opencode "Quick fix in file.py"

# Parallel execution (fire and forget)
emrakul delegate kimi "Research A" --bg &
emrakul delegate kimi "Research B" --bg &
emrakul delegate cursor "Implement C" --bg &

# Check results
emrakul status all
cat ~/.emrakul/outputs/{task-id}.json
```

## Workers
| Worker | Model | Use For |
|--------|-------|---------|
| cursor | Opus 4.5 | Implementation, refactors, multi-file (PRIMARY) |
| codex | GPT-5.2 Codex | Debugging, tests, recursive tracing |
| kimi | Kimi K2.5 | Internet research, documentation |
| opencode | ZAI GLM 4.7 | Quick single-file edits |

## Devices
- `--device local` - MacBook (Apple Silicon, Metal)
- `--device theodolos` - Remote (NVIDIA GPU, CUDA)
</emrakul-cli>

<testing-requirement>
Tests are MANDATORY. No implementation without tests.
1. Delegate implementation to Cursor/OpenCode
2. Delegate test writing to Codex
3. Run: `uv run pytest` and `uv run ruff check . --fix`
4. Both must pass before work is done
</testing-requirement>

<python>
UV only. Never bare python/pip.
- uv run script.py
- uv add package
- uv run pytest
</python>
