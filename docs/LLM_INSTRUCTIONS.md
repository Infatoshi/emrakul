# Emrakul - LLM Instructions

You are reading this because you are an AI agent (likely Claude Code) working in a repository that uses Emrakul for agent orchestration.

## Critical Rule

**DO NOT USE THE NATIVE TASK TOOL.**

The Task tool burns 20x quota per call. A PreToolUse hook blocks it, but if you somehow bypass it, you will cause rate limit issues for the user.

## What To Use Instead

Use the Emrakul CLI (installed globally via `uv tool install`):

```bash
emrakul delegate cursor "task"   # Implementation (Opus 4.6) - PRIMARY
emrakul delegate codex "task"    # Tests, debugging (GPT-5.3 Codex)
emrakul delegate kimi "task"     # Internet research (Kimi K2.5)
emrakul delegate opencode "task" # Quick edits (ZAI GLM 4.7)
```

## When To Delegate vs Do Directly

**Do directly** (use native Edit/Read/Write/Bash):
- Simple file reads
- Small edits (< 20 lines)
- Running commands
- Git operations

**Delegate** (use Emrakul CLI):
- Multi-file implementations
- Writing comprehensive tests
- Debugging complex issues
- Internet research
- Any task that would benefit from parallel execution

## Parallel Execution

Use Claude Code's native `run_in_background=True` for parallel execution:

```python
# Launch multiple tasks in parallel (all return immediately with task IDs)
Bash(command='emrakul delegate kimi "Research GPU fundamentals" --json', run_in_background=True)
Bash(command='emrakul delegate kimi "Research aerospace GPU" --json', run_in_background=True)
Bash(command='emrakul delegate cursor "Implement feature X" --json', run_in_background=True)

# Continue working on other things...

# When notified of completion, read results
TaskOutput(task_id="abc123", block=False)
```

This is the preferred pattern because:
- Tasks run truly in parallel (not sequential)
- Claude Code tracks tasks and notifies on completion
- No manual file checking needed - use TaskOutput to read results
- Task IDs let you track multiple concurrent delegations

## CLI Options

```
emrakul delegate <worker> "task"
  --device local|theodolos   # Where to run (default: local)
  --dir /path/to/project     # Working directory
  --files file1.py file2.py  # Context files (cursor/codex/opencode)
  --bg                       # Background mode
  --output /path/to/out.json # Custom output file
  --json                     # JSON output format
```

## Device Selection

- `--device local` - MacBook (Apple Silicon, Metal)
- `--device theodolos` - Remote workstation (NVIDIA GPU, CUDA)

Use theodolos for:
- GPU-accelerated work
- Large model inference
- CUDA kernel development

## Testing Requirements

All delegated implementation work MUST include tests:
1. Include "write tests" in the task prompt, OR
2. Follow up with a `delegate codex` task specifically for tests

Verification:
```bash
uv run pytest
uv run ruff check . --fix
```

## Python

Use `uv` for everything:
- `uv run script.py` (not `python script.py`)
- `uv add package` (not `pip install`)
- `uv run pytest` (not `pytest`)

## Restrictions

- No emojis in code or comments
- No em dashes
- Never guess performance numbers - benchmark or say "needs measurement"
- Do not over-engineer
- Do not add features beyond the task
