"""Worker adapters for external AI CLIs.

Each worker type has a specialized system prompt and execution method.
Workers are stateless - they execute a single task and return the result.

All workers run in yolo/bypass permissions mode - no approval needed.
"""

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class WorkerResult:
    """Result from a worker execution."""

    success: bool
    output: str
    error: Optional[str] = None
    backend: str = ""


# Load prompts from files
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(worker: str) -> str:
    """Load system prompt for a worker type."""
    prompt_file = PROMPTS_DIR / f"{worker}.md"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return ""


async def run_codex(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    timeout: int = 600,
) -> WorkerResult:
    """Run task with Codex CLI.

    Best for: deep debugging, recursive call tracing, complex logic.
    Uses: codex exec (non-interactive)
    """
    codex_path = shutil.which("codex")
    if not codex_path:
        return WorkerResult(success=False, output="", error="Codex CLI not found", backend="codex")

    prompt = _build_prompt("codex", task, context_files)
    cwd = Path(working_dir) if working_dir else Path.cwd()

    # codex exec runs non-interactively
    # Full disk read access for debugging
    cmd = [
        codex_path,
        "exec",
        "-c", 'sandbox_permissions=["disk-full-read-access", "disk-write-cwd"]',
        prompt,
    ]

    return await _run_command(cmd, cwd, timeout, "codex")


async def run_gemini(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    timeout: int = 600,
) -> WorkerResult:
    """Run task with Gemini CLI.

    Best for: tests, documentation, frontend, performance optimization.
    Uses: --yolo for auto-approval, -o json for structured output
    """
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        return WorkerResult(success=False, output="", error="Gemini CLI not found", backend="gemini")

    prompt = _build_prompt("gemini", task, context_files)
    cwd = Path(working_dir) if working_dir else Path.cwd()

    # --yolo bypasses all approval prompts
    cmd = [
        gemini_path,
        "--yolo",
        "-o", "json",
        prompt,
    ]

    return await _run_command(cmd, cwd, timeout, "gemini")


async def run_kimi(
    task: str,
    timeout: int = 600,
) -> WorkerResult:
    """Run task with Kimi CLI.

    Best for: deep internet research, finding documentation, understanding systems.
    No context files - Kimi researches online.
    Uses: --print for non-interactive mode
    """
    kimi_path = shutil.which("kimi")
    if not kimi_path:
        return WorkerResult(success=False, output="", error="Kimi CLI not found", backend="kimi")

    prompt = _build_prompt("kimi", task, None)

    # --print enables non-interactive mode (implicitly yolo)
    # Empty MCP config to avoid slow startup
    empty_mcp = Path("/tmp/emrakul-kimi-empty-mcp.json")
    if not empty_mcp.exists():
        empty_mcp.write_text('{"mcpServers":{}}')

    cmd = [
        kimi_path,
        "-p", prompt,
        "--print",
        "--mcp-config-file", str(empty_mcp),
    ]

    return await _run_command(cmd, Path.cwd(), timeout, "kimi")


async def run_opencode(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    timeout: int = 600,
) -> WorkerResult:
    """Run task with OpenCode CLI.

    Best for: general implementation, quick fixes, boilerplate.
    """
    opencode_path = shutil.which("opencode")
    if not opencode_path:
        return WorkerResult(
            success=False, output="", error="OpenCode CLI not found", backend="opencode"
        )

    prompt = _build_prompt("opencode", task, context_files)
    cwd = Path(working_dir) if working_dir else Path.cwd()

    # Prepend working dir since opencode run lacks --cwd
    full_prompt = f"Working directory: {cwd}\n\n{prompt}"
    cmd = [opencode_path, "run", "--format", "json", full_prompt]

    return await _run_command(cmd, cwd, timeout, "opencode")


async def run_cursor(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    timeout: int = 600,
) -> WorkerResult:
    """Run task with Cursor CLI agent mode.

    Best for: complex multi-file tasks, large context, when you have $20k credits.
    Uses: --print --force for non-interactive yolo mode
    """
    cursor_path = shutil.which("cursor")
    if not cursor_path:
        return WorkerResult(success=False, output="", error="Cursor CLI not found", backend="cursor")

    prompt = _build_prompt("cursor", task, context_files)
    cwd = Path(working_dir) if working_dir else Path.cwd()

    # --print: non-interactive, has access to all tools
    # --force: force allow commands (yolo mode)
    # --output-format json: structured output
    # --workspace: set working directory
    cmd = [
        cursor_path,
        "agent",
        "--print",
        "--force",
        "--output-format", "json",
        "--workspace", str(cwd),
        prompt,
    ]

    return await _run_command(cmd, cwd, timeout, "cursor")


def _build_prompt(worker: str, task: str, context_files: Optional[list[str]]) -> str:
    """Build full prompt with system context and file contents."""
    system_prompt = load_prompt(worker)
    parts = []

    if system_prompt:
        parts.append(system_prompt)

    parts.append(f"Task:\n{task}")

    if context_files:
        parts.append("Relevant files:")
        for f in context_files:
            path = Path(f)
            if path.exists():
                content = path.read_text()
                # Truncate large files to avoid token bloat
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                parts.append(f"--- {f} ---\n{content}")

    return "\n\n".join(parts)


async def _run_command(
    cmd: list[str],
    cwd: Path,
    timeout: int,
    backend: str,
) -> WorkerResult:
    """Execute command and capture output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        if proc.returncode != 0:
            return WorkerResult(
                success=False,
                output=stdout.decode(),
                error=stderr.decode(),
                backend=backend,
            )

        return WorkerResult(
            success=True,
            output=stdout.decode(),
            backend=backend,
        )

    except asyncio.TimeoutError:
        return WorkerResult(
            success=False,
            output="",
            error=f"Timeout after {timeout}s",
            backend=backend,
        )
    except Exception as e:
        return WorkerResult(
            success=False,
            output="",
            error=str(e),
            backend=backend,
        )
