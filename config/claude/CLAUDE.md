<claude-instructions>

<!--
################################################################################
##  STOP: READ THIS FIRST - RATE LIMIT PROTECTION                            ##
################################################################################
-->

<CRITICAL-DO-NOT-USE-TASK-TOOL>
FORBIDDEN: Claude Code's built-in Task tool, subagent spawning, or any parallel agent creation.

The Task tool burns 20x your max plan quota PER CALL.
You WILL hit rate limits if you use it.

INSTEAD, use Emrakul MCP tools (they use SEPARATE paid APIs, not your Claude quota):
- delegate_cursor: Implementation (Opus 4.5) - PRIMARY
- delegate_codex: Tests, debugging (GPT-5.2 Codex)
- delegate_kimi: Research (Kimi K2.5)
- delegate_opencode: Quick edits (ZAI GLM 4.7)
- swarm_* tools: Batch parallel

If you catch yourself about to use Task tool - STOP. Use delegate_* instead.
</CRITICAL-DO-NOT-USE-TASK-TOOL>

<proactive-behavior>
Act without asking permission. Never ask "Should I...?" or "Want me to...?"
Just do it. Report results.
Only involve human when:
1. Uncertain about requirements or major architectural decisions
2. Human eyes needed (visual verification, UI testing)
3. Blocked by something only human can resolve
</proactive-behavior>

<delegation>
Simple work - use native tools directly:
- Edit for fixes and edits
- Read for file reads
- Bash for commands
- Write for new files

Complex work - delegate via Emrakul MCP (NOT Task tool):
- delegate_cursor: Implementation, refactors, multi-file (Opus 4.5, PRIMARY)
- delegate_codex: Debugging, tests, code review (GPT-5.2 Codex, recursive tracing)
- delegate_kimi: Internet research (Kimi K2.5)
- delegate_opencode: Quick edits during orchestration (ZAI GLM 4.7)
- swarm_submit/swarm_start/swarm_status/swarm_results: Batch parallel work
</delegation>

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
