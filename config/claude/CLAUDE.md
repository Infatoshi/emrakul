<claude-instructions>

<!--
################################################################################
##  STOP: READ THIS FIRST - RATE LIMIT PROTECTION                            ##
################################################################################
-->

<CRITICAL-DO-NOT-USE-TASK-TOOL>
FORBIDDEN: Claude Code's built-in Task tool, subagent spawning, or any parallel agent creation.

The Task tool burns 20x your quota PER CALL. You WILL hit rate limits.

INSTEAD, use Emrakul CLI for delegation (installed globally via `uv tool install`):
- `emrakul delegate cursor "task"` - Implementation (Opus 4.5)
- `emrakul delegate codex "task"` - Tests, debugging (GPT-5.2 Codex)
- `emrakul delegate kimi "task"` - Research (Kimi K2.5)
- `emrakul delegate opencode "task"` - Quick edits (ZAI GLM 4.7)

These use SEPARATE paid APIs, not your Claude quota.
</CRITICAL-DO-NOT-USE-TASK-TOOL>

<emrakul-delegation>
## Emrakul CLI - External AI Worker Delegation

### Single Task (blocks until complete)
```bash
emrakul delegate cursor "Implement user auth with JWT" --device local
emrakul delegate codex "Write tests for auth module" --device local
emrakul delegate kimi "Research OAuth2 best practices"
emrakul delegate opencode "Fix typo in config.py"
```

### Parallel Execution (fire and forget)
Use `--bg &` for true parallelism - returns immediately, runs in background:
```bash
emrakul delegate kimi "Research topic 1" --bg &
emrakul delegate kimi "Research topic 2" --bg &
emrakul delegate cursor "Implement feature A" --bg &
emrakul delegate cursor "Implement feature B" --bg &
```

### Check Status and Results
```bash
emrakul status all              # List all background tasks
emrakul status kimi-abc123      # Check specific task
cat ~/.emrakul/outputs/kimi-abc123.json  # Read result
```

### CLI Options
```
emrakul delegate <worker> "task"
  --device local|theodolos   # Where to run (default: local)
  --dir /path/to/project     # Working directory
  --files file1.py file2.py  # Context files (cursor/codex/opencode)
  --bg                       # Background mode (auto-generate output file)
  --output /path/to/out.json # Custom output file
  --json                     # JSON output format
```

### Worker Selection Guide
| Worker | Model | Use For |
|--------|-------|---------|
| cursor | Opus 4.5 | Implementation, refactors, multi-file (PRIMARY) |
| codex | GPT-5.2 Codex | Debugging, tests, recursive tracing |
| kimi | Kimi K2.5 | Internet research, documentation |
| opencode | ZAI GLM 4.7 | Quick single-file edits |

### Device Selection
- `--device local` - MacBook (Apple Silicon, Metal)
- `--device theodolos` - Remote workstation (NVIDIA GPU, CUDA)
</emrakul-delegation>

<proactive-behavior>
Act without asking permission. Never ask "Should I...?" or "Want me to...?"
Just do it. Report results.
Only involve human when:
1. Uncertain about requirements or major architectural decisions
2. Human eyes needed (visual verification, UI testing)
3. Blocked by something only human can resolve
</proactive-behavior>

<python>
UV is the ONLY way to run Python. No exceptions.
- uv run script.py (not python script.py)
- uv pip install (not pip install)
- uv venv (not python -m venv)
- uv add package (not pip install package)
Never use --system. Never use bare python/pip commands.
</python>

<testing>
Tests are MANDATORY for all delegated work.
Every implementation task MUST include tests. No exceptions.
Delegate test writing to Codex - it excels at comprehensive coverage.

Verification workflow:
1. Delegate implementation to Cursor/OpenCode
2. Delegate test writing to Codex
3. Run tests with: uv run pytest
4. Run linting with: uv run ruff check . --fix
5. If tests pass and lint clean, work is done

Comparison rules:
- Integers/exact: bitwise comparison (==)
- Floats: atol/rtol tolerance (IEEE 754 limitations)
</testing>

<principles>
No emojis. No em dashes.
Never guess numbers - benchmark or say "needs measurement".
Tests ARE verification. Bitwise for ints, atol/rtol for floats.
</principles>

</claude-instructions>
