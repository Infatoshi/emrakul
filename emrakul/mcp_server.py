"""Emrakul MCP Server - Agent delegation for Claude Code.

Exposes tools for:
- Ad-hoc delegation to specialized workers (Codex, Kimi, Cursor, OpenCode)
- Swarm execution with backend-specific task routing
- Device routing (local MacBook or remote Theodolos)

Workers:
- Codex: debugging + tests (GPT-5.2)
- Kimi: research, finding documentation
- Cursor: implementation (Opus 4.5, $20k credits)
- OpenCode: quick edits (xAI GLM 4.7)

Run with: uv run python -m emrakul.mcp_server
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from emrakul.swarm import get_swarm
from emrakul.workers import run_codex, run_cursor, run_kimi, run_opencode

mcp = FastMCP("emrakul")

# Default timeout for worker calls
DEFAULT_TOOL_TIMEOUT = 300  # 5 min for most workers
CURSOR_TIMEOUT = None  # No timeout for Cursor - complex work takes as long as it takes


def _safe_json_response(success: bool, output: str = "", error: str = "", **kwargs) -> str:
    """Create a safe JSON response, handling any serialization issues."""
    try:
        return json.dumps({
            "success": success,
            "output": output,
            "error": error,
            **kwargs
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "output": "",
            "error": f"Serialization error: {str(e)}"
        })


# =============================================================================
# Ad-hoc Delegation Tools
# =============================================================================


@mcp.tool()
async def delegate_codex(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    device: str = "local",
    timeout: int = DEFAULT_TOOL_TIMEOUT,
) -> str:
    """Delegate a task to Codex (GPT-5.2) for debugging or writing tests.

    Best for:
    - Debugging: recursive call tracing, finding root causes
    - Writing tests: comprehensive test suites with edge cases
    - Understanding complex control flow
    - Tracing data through multiple transformations

    Args:
        task: The task description - be specific about what to debug or test
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task
        device: "local" (MacBook) or "theodolos" (remote GPU machine)
        timeout: Timeout in seconds (default 300)

    Returns:
        Codex's analysis, tests, or findings
    """
    try:
        result = await asyncio.wait_for(
            run_codex(task, context_files, working_dir, device, timeout=timeout),
            timeout=timeout + 30  # Extra buffer for cleanup
        )
        return _safe_json_response(
            success=result.success,
            output=result.output,
            error=result.error or "",
            device=result.device,
        )
    except asyncio.TimeoutError:
        return _safe_json_response(False, error=f"Timeout after {timeout}s", device=device)
    except Exception as e:
        return _safe_json_response(False, error=f"Error: {str(e)}", device=device)


@mcp.tool()
async def delegate_kimi(
    task: str,
    device: str = "local",
    timeout: int = DEFAULT_TOOL_TIMEOUT,
) -> str:
    """Delegate a research task to Kimi for deep internet research.

    Best for:
    - Finding implementation details in documentation
    - Researching how existing systems work internally
    - Locating reference implementations and code examples
    - Understanding APIs and their edge cases

    Args:
        task: The research question - be specific about what you need to learn
        device: "local" (MacBook) or "theodolos" (remote machine)
        timeout: Timeout in seconds (default 300)

    Returns:
        Kimi's research findings with source citations
    """
    try:
        result = await asyncio.wait_for(
            run_kimi(task, device, timeout=timeout),
            timeout=timeout + 30
        )
        return _safe_json_response(
            success=result.success,
            output=result.output,
            error=result.error or "",
            device=result.device,
        )
    except asyncio.TimeoutError:
        return _safe_json_response(False, error=f"Timeout after {timeout}s", device=device)
    except Exception as e:
        return _safe_json_response(False, error=f"Error: {str(e)}", device=device)


@mcp.tool()
async def delegate_opencode(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    device: str = "local",
    timeout: int = 180,
) -> str:
    """Delegate a task to OpenCode for quick edits and small fixes.

    Best for:
    - Quick single-file edits
    - Small bug fixes
    - Fast turnaround tasks
    - Simple refactors

    Args:
        task: The task description - keep it focused and specific
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task
        device: "local" (MacBook) or "theodolos" (remote GPU machine)
        timeout: Timeout in seconds (default 180 for quick edits)

    Returns:
        OpenCode's output
    """
    try:
        result = await asyncio.wait_for(
            run_opencode(task, context_files, working_dir, device, timeout=timeout),
            timeout=timeout + 30
        )
        return _safe_json_response(
            success=result.success,
            output=result.output,
            error=result.error or "",
            device=result.device,
        )
    except asyncio.TimeoutError:
        return _safe_json_response(False, error=f"Timeout after {timeout}s", device=device)
    except Exception as e:
        return _safe_json_response(False, error=f"Error: {str(e)}", device=device)


@mcp.tool()
async def delegate_cursor(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    device: str = "local",
    timeout: Optional[int] = CURSOR_TIMEOUT,
) -> str:
    """Delegate a task to Cursor (Opus 4.5) for implementation work.

    PRIMARY IMPLEMENTATION WORKER - $20k credits available.

    Best for:
    - General implementation (preferred over other workers)
    - Complex tasks spanning many files
    - Large refactors requiring coordination
    - Quick fixes and bug repairs
    - Any coding task that doesn't specifically need debugging or tests

    Args:
        task: The task description - can be complex multi-step work
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task
        device: "local" (MacBook) or "theodolos" (remote GPU machine)
        timeout: Timeout in seconds (default None - no timeout)

    Returns:
        Cursor's implementation
    """
    try:
        # No timeout wrapper for Cursor - let it run as long as needed
        result = await run_cursor(task, context_files, working_dir, device, timeout=timeout)
        return _safe_json_response(
            success=result.success,
            output=result.output,
            error=result.error or "",
            device=result.device,
        )
    except Exception as e:
        return _safe_json_response(False, error=f"Error: {str(e)}", device=device)


# =============================================================================
# Swarm Tools - Batch parallel execution with backend routing
# =============================================================================


@mcp.tool()
async def swarm_submit(tasks_yaml: str) -> str:
    """Submit batch tasks to the Emrakul swarm for parallel execution.

    Each task is routed to its assigned backend (codex, kimi, cursor, opencode).
    Tasks run in priority order (P0 first) with dependency resolution.

    YAML format:
    ```yaml
    tasks:
      - name: fix-auth-bug
        prompt: Fix the authentication bug in login.py
        backend: codex      # codex, kimi, cursor, or opencode
        priority: P0        # P0 (critical) to P3 (low)
        device: local       # local or theodolos
        verify: pytest tests/test_auth.py  # optional verification
        dependencies: []    # other task names to wait for

      - name: quick-fix
        prompt: Fix the typo in utils.py
        backend: opencode
        priority: P1
        dependencies: [fix-auth-bug]
    ```

    Args:
        tasks_yaml: YAML content defining tasks (not a file path)

    Returns:
        Submission status with task count
    """
    try:
        swarm = get_swarm()
        tasks = swarm.add_tasks_from_string(tasks_yaml)

        return json.dumps({
            "status": "submitted",
            "tasks_added": len(tasks),
            "task_names": [t.name for t in tasks],
            "swarm_running": swarm.running,
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def swarm_submit_file(tasks_yaml_path: str) -> str:
    """Submit batch tasks from a YAML file to the Emrakul swarm.

    See swarm_submit for YAML format.

    Args:
        tasks_yaml_path: Path to YAML file containing task definitions

    Returns:
        Submission status with task count
    """
    try:
        path = Path(tasks_yaml_path)
        if not path.exists():
            return json.dumps({"status": "error", "error": f"File not found: {tasks_yaml_path}"})

        swarm = get_swarm()
        tasks = swarm.add_tasks_from_yaml(str(path))

        return json.dumps({
            "status": "submitted",
            "tasks_added": len(tasks),
            "task_names": [t.name for t in tasks],
            "swarm_running": swarm.running,
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def swarm_start(num_workers: int = 5) -> str:
    """Start the swarm with N concurrent workers.

    Workers pull tasks from the queue and execute them on their
    assigned backends. Start after submitting tasks.

    Args:
        num_workers: Number of concurrent workers (default 5)

    Returns:
        Swarm status
    """
    try:
        swarm = get_swarm()
        await swarm.start(num_workers)

        return json.dumps({
            "status": "started",
            "workers": num_workers,
            **swarm.status(),
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def swarm_stop() -> str:
    """Stop the swarm.

    Running tasks will complete, but no new tasks will be started.

    Returns:
        Final swarm status
    """
    try:
        swarm = get_swarm()
        status = swarm.status()
        await swarm.stop()

        return json.dumps({
            "status": "stopped",
            **status,
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
def swarm_status() -> str:
    """Check swarm status.

    Returns:
        Status including pending, in_progress, completed, failed counts,
        and breakdown by backend.
    """
    try:
        swarm = get_swarm()
        return json.dumps(swarm.status())
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
def swarm_results(include_pending: bool = False) -> str:
    """Get task results from the swarm.

    Args:
        include_pending: Include pending tasks in results (default False)

    Returns:
        List of task results with status, output, and errors
    """
    try:
        swarm = get_swarm()
        results = swarm.results(include_pending)
        return json.dumps({"results": results, "count": len(results)})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
def swarm_clear() -> str:
    """Clear all tasks from the swarm.

    Use after reviewing results to reset for next batch.

    Returns:
        Confirmation
    """
    try:
        swarm = get_swarm()
        swarm.clear()
        return json.dumps({"status": "cleared"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
def health() -> str:
    """Check if the Emrakul MCP server is responsive.

    Returns:
        Status confirmation with swarm state
    """
    try:
        swarm = get_swarm()
        return json.dumps({
            "status": "healthy",
            "swarm_running": swarm.running,
            "swarm_tasks": len(swarm.tasks),
        })
    except Exception as e:
        return json.dumps({"status": "degraded", "error": str(e)})


def main():
    """Run the MCP server."""
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Log to stderr so it doesn't break stdio protocol
        print(f"MCP server error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
