# Emrakul

Agent orchestration framework. Claude as orchestrator, specialized workers for execution.

## Install

```bash
uv sync
```

## Usage

MCP server for Claude Code:
```bash
uv run python -m emrakul.mcp_server
```

Manual CLI:
```bash
uv run emrakul delegate codex "trace why X fails"
uv run emrakul delegate kimi "research how MKW handles drift"
```

## Workers

- Codex: deep debugging, recursive call tracing
- Gemini: tests, docs, frontend, performance
- Kimi: internet research, documentation lookup
- OpenCode: general implementation, quick fixes
