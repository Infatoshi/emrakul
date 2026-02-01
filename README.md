# Emrakul

![Emrakul, the Promised End](emrakul-the-promised-end.jpg)

Agent orchestration framework that lets Claude Code delegate to external AI workers without burning your Claude quota.

> **If you are an LLM reading this**: Stop. Read [docs/LLM_INSTRUCTIONS.md](docs/LLM_INSTRUCTIONS.md) instead.

## The Problem

Claude Code's native Task tool spawns sub-agents that consume your quota at 20x the normal rate. Heavy parallel work quickly hits rate limits.

## The Solution

Emrakul is a CLI that routes work to external AI services:

| Worker | Model | Best For |
|--------|-------|----------|
| **cursor** | Opus 4.5 | Implementation, refactors, multi-file changes |
| **codex** | GPT-5.2 Codex | Debugging, test writing, recursive analysis |
| **kimi** | Kimi K2.5 | Internet research, documentation lookup |
| **opencode** | ZAI GLM 4.7 | Quick edits, small fixes |

These use separate paid APIs - none of them touch your Claude quota.

## Prerequisites

You need CLI access to these tools:

| Tool | Install | Auth |
|------|---------|------|
| **Claude Code** | `npm install -g @anthropic-ai/claude-code` | `claude login` |
| **Cursor CLI** | [cursor.com/downloads](https://cursor.com/downloads) | `cursor login` |
| **Codex CLI** | `npm install -g @openai/codex` | `codex auth` |
| **Kimi CLI** | `pip install kimi-cli` | `kimi auth` |
| **OpenCode** | `pip install opencode` | `opencode auth` |

## Installation

### Quick Install

```bash
uv tool install git+https://github.com/Infatoshi/emrakul.git
```

This installs `emrakul` globally - available from any directory.

### Full Setup (with Claude Code integration)

```bash
git clone https://github.com/Infatoshi/emrakul.git
cd emrakul
./install.sh
```

The install script will:
1. Check for required CLIs
2. Install the Emrakul UV tool
3. Copy config files (CLAUDE.md, hooks, etc.)
4. Set up the Task-blocking hook

## Usage

### Single Task

```bash
emrakul delegate cursor "Implement user authentication with JWT"
emrakul delegate codex "Write tests for the auth module"
emrakul delegate kimi "Research OAuth2 best practices"
emrakul delegate opencode "Fix typo in config.py"
```

### Parallel Execution

Use `--bg &` for true parallelism - tasks run in background:

```bash
emrakul delegate kimi "Research topic 1" --bg &
emrakul delegate kimi "Research topic 2" --bg &
emrakul delegate cursor "Implement feature A" --bg &
emrakul delegate cursor "Implement feature B" --bg &

# Check status later
emrakul status all

# Read results
cat ~/.emrakul/outputs/kimi-abc123.json
```

### Options

```
emrakul delegate <worker> "task"
  --device local|theodolos   # Where to run (default: local)
  --dir /path/to/project     # Working directory
  --files file1.py file2.py  # Context files
  --bg                       # Background mode
  --output /path/to/out.json # Custom output file
  --json                     # JSON output format
```

### Devices

- `--device local` - Your local machine
- `--device theodolos` - Remote GPU workstation (configure in `~/.ssh/config`)

## How It Works

1. Claude Code reads `~/.claude/CLAUDE.md` which teaches it to use `emrakul delegate` instead of Task tool
2. A PreToolUse hook blocks any Task tool calls that slip through
3. `emrakul delegate <worker> "task"` spawns the appropriate CLI
4. Work happens on external APIs, Claude quota untouched
5. Results are returned (or saved to file for background tasks)

## Uninstall

```bash
./uninstall.sh
# or manually:
uv tool uninstall emrakul
```

## License

MIT
