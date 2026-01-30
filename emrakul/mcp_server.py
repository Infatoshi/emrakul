"""Emrakul MCP Server - Agent delegation for Claude Code.

Exposes tools for:
- Ad-hoc delegation to specialized workers (Codex, Gemini, Kimi, OpenCode, Cursor)
- Pool submission for batch parallel work (connects to AlphaHENG if available)

Run with: uv run python -m emrakul.mcp_server
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from emrakul.workers import run_codex, run_cursor, run_gemini, run_kimi, run_opencode

mcp = FastMCP("emrakul")


@mcp.tool()
async def delegate_codex(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
) -> str:
    """Delegate a task to Codex for deep debugging or complex logic tracing.

    Best for:
    - Recursive call tracing to find root causes
    - Debugging divergences between expected and actual behavior
    - Understanding complex control flow
    - Tracing data through multiple transformations

    Args:
        task: The task description - be specific about what to trace or debug
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task (defaults to current)

    Returns:
        Codex's analysis and findings
    """
    result = await run_codex(task, context_files, working_dir)
    return json.dumps({
        "success": result.success,
        "output": result.output,
        "error": result.error,
    })


@mcp.tool()
async def delegate_gemini(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
) -> str:
    """Delegate a task to Gemini for tests, docs, frontend, or performance work.

    Best for:
    - Writing comprehensive test suites with edge cases
    - Technical documentation with examples
    - Frontend implementation and component design
    - Performance optimization and profiling
    - Tasks requiring very long context

    Args:
        task: The task description
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task (defaults to current)

    Returns:
        Gemini's implementation or analysis
    """
    result = await run_gemini(task, context_files, working_dir)
    return json.dumps({
        "success": result.success,
        "output": result.output,
        "error": result.error,
    })


@mcp.tool()
async def delegate_kimi(task: str) -> str:
    """Delegate a research task to Kimi for deep internet research.

    Best for:
    - Finding implementation details in documentation
    - Researching how existing systems work internally
    - Locating reference implementations and code examples
    - Understanding APIs and their edge cases
    - Synthesizing information from multiple sources

    Args:
        task: The research question or topic - be specific about what you need to learn

    Returns:
        Kimi's research findings with source citations
    """
    result = await run_kimi(task)
    return json.dumps({
        "success": result.success,
        "output": result.output,
        "error": result.error,
    })


@mcp.tool()
async def delegate_opencode(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
) -> str:
    """Delegate a task to OpenCode for general implementation or quick fixes.

    Best for:
    - Straightforward implementations following existing patterns
    - Quick bug fixes with minimal diff
    - Boilerplate generation
    - Porting code between similar languages
    - Repetitive tasks

    Args:
        task: The task description - include specific file paths and expected behavior
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task (defaults to current)

    Returns:
        OpenCode's implementation
    """
    result = await run_opencode(task, context_files, working_dir)
    return json.dumps({
        "success": result.success,
        "output": result.output,
        "error": result.error,
    })


@mcp.tool()
async def delegate_cursor(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
) -> str:
    """Delegate a task to Cursor for complex multi-file implementations.

    Best for:
    - Complex tasks spanning many files
    - Large refactors requiring coordination
    - Tasks needing large context window
    - When you have Cursor credits to burn ($20k available)

    Runs in yolo mode with --force flag. No approval needed.

    Args:
        task: The task description - can be complex multi-step work
        context_files: Optional list of file paths to include as context
        working_dir: Working directory for the task (defaults to current)

    Returns:
        Cursor's implementation
    """
    result = await run_cursor(task, context_files, working_dir)
    return json.dumps({
        "success": result.success,
        "output": result.output,
        "error": result.error,
    })


@mcp.tool()
def pool_submit(tasks_yaml_path: str) -> str:
    """Submit batch tasks to AlphaHENG worker pool for parallel execution.

    Use for:
    - Parallelizable work with oracle verification
    - Porting codebases with many similar transformations
    - Implementing many functions from headers
    - Kernel optimization with high variance across attempts
    - Any task where rejection sampling improves results

    Requires AlphaHENG to be installed and configured.

    Args:
        tasks_yaml_path: Path to YAML file containing task definitions

    Returns:
        Submission status and queue depth
    """
    path = Path(tasks_yaml_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {tasks_yaml_path}"})

    result = subprocess.run(
        ["uv", "run", "alphaheng", "tasks", "add", str(path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return json.dumps({"error": result.stderr, "status": "failed"})

    return json.dumps({"status": "submitted", "output": result.stdout.strip()})


@mcp.tool()
def pool_status() -> str:
    """Check AlphaHENG worker pool status.

    Returns queue depth, active workers, and recent completions.
    Requires AlphaHENG to be running.

    Returns:
        Pool status including pending tasks, active workers, completed count
    """
    result = subprocess.run(
        ["uv", "run", "alphaheng", "status"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return json.dumps({"error": result.stderr, "status": "unavailable"})

    return json.dumps({"status": "available", "output": result.stdout.strip()})


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
