# Emrakul - LLM Instructions

You are reading this because you are an AI agent (likely Claude Code) working in a repository that uses Emrakul for agent orchestration.

## Critical Rule

**DO NOT USE THE NATIVE TASK TOOL.**

The Task tool burns 20x quota per call. A PreToolUse hook blocks it, but if you somehow bypass it, you will cause rate limit issues for the user.

## What To Use Instead

Use Emrakul MCP tools for all delegation:

| Tool | Use For |
|------|---------|
| `delegate_cursor` | Implementation, refactors, multi-file (Opus 4.5, PRIMARY) |
| `delegate_codex` | Tests, debugging, recursive analysis (GPT-5.2 Codex) |
| `delegate_kimi` | Internet research (Kimi K2.5) |
| `delegate_opencode` | Quick single-file edits (ZAI GLM 4.7) |
| `swarm_submit` | Batch parallel tasks (YAML format) |
| `swarm_start` | Start swarm workers |
| `swarm_status` | Check swarm progress |
| `swarm_results` | Get completed task outputs |
| `swarm_clear` | Clear task queue |

## When To Delegate vs Do Directly

**Do directly** (use native Edit/Read/Write/Bash):
- Simple file reads
- Small edits (< 20 lines)
- Running commands
- Git operations

**Delegate** (use Emrakul MCP):
- Multi-file implementations
- Writing comprehensive tests
- Debugging complex issues
- Internet research
- Any task that would benefit from parallel execution

## Delegation Examples

### Single Task
```python
delegate_cursor(
    task="Implement user authentication with JWT",
    working_dir="/path/to/project",
    device="local"  # or "theodolos" for GPU work
)
```

### Batch Parallel
```python
swarm_submit(tasks_yaml="""
tasks:
  - name: implement-api
    prompt: Add REST API for users
    backend: cursor
    priority: P0

  - name: write-tests
    prompt: Write tests for user API
    backend: codex
    priority: P1
    dependencies: [implement-api]
""")
swarm_start(num_workers=3)
# ... later ...
swarm_status()
swarm_results()
```

## Device Selection

- `device="local"` - MacBook, Apple Silicon, Metal
- `device="theodolos"` - Remote workstation, NVIDIA GPU, CUDA

Use theodolos for:
- GPU-accelerated work
- Large model inference
- CUDA kernel development

## Testing Requirements

All delegated implementation work MUST include tests:
1. Include "write tests" in the task prompt, OR
2. Follow up with a `delegate_codex` task specifically for tests

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

## Workflow

1. Understand the task
2. Decide: direct edit or delegation?
3. If delegating, choose the right worker
4. If parallel tasks, use swarm
5. After delegation completes, verify with tests
6. Run linting
7. Report results
