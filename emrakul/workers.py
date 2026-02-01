"""Worker adapters for external AI CLIs.

Each worker type has a specialized system prompt and execution method.
Workers are stateless - they execute a single task and return the result.

All workers run in yolo/bypass permissions mode - no approval needed.
Supports local and remote (Theodolos) execution via device parameter.

Model specifications:
- Cursor: opus-4.5-thinking (Opus 4.5 Thinking, $20k credits)
- OpenCode: zai-coding-plan/glm-4.7 (xAI GLM 4.7, $200/month plan)
- Codex: gpt-5.2-codex (GPT-5.2, xhigh reasoning)
- Kimi: default (kimi-for-coding, powered by Kimi K2.5)
"""

import asyncio
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Remote machine config
THEODOLOS_HOST = "theodolos"  # SSH config name
THEODOLOS_BIN = "/home/infatoshi/.local/bin"  # CLI binaries location

# Model configurations
CURSOR_MODEL = "opus-4.5-thinking"
OPENCODE_MODEL = "zai-coding-plan/glm-4.7"
CODEX_MODEL = "gpt-5.2-codex"


@dataclass
class WorkerResult:
    """Result from a worker execution."""

    success: bool
    output: str
    error: Optional[str] = None
    backend: str = ""
    device: str = "local"


# Load prompts from files
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(worker: str) -> str:
    """Load system prompt for a worker type."""
    prompt_file = PROMPTS_DIR / f"{worker}.md"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return ""


def _parse_codex_output(raw: str) -> str:
    """Parse Codex JSONL output, extract text from item.completed events."""
    texts = []
    for line in raw.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "item.completed":
                item = data.get("item", {})
                if text := item.get("text"):
                    texts.append(text)
        except json.JSONDecodeError:
            continue
    return "\n".join(texts) if texts else raw


def _parse_kimi_output(raw: str) -> str:
    """Parse Kimi JSON output, extract text content."""
    try:
        data = json.loads(raw)
        contents = data.get("content", [])
        texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
        return "\n".join(texts) if texts else raw
    except json.JSONDecodeError:
        return raw


def _parse_cursor_output(raw: str) -> str:
    """Parse Cursor JSON output, extract result field."""
    try:
        data = json.loads(raw)
        return data.get("result", raw)
    except json.JSONDecodeError:
        return raw


def _parse_opencode_output(raw: str) -> str:
    """Parse OpenCode JSONL output, extract text from text events."""
    texts = []
    for line in raw.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "text":
                part = data.get("part", {})
                if text := part.get("text"):
                    texts.append(text)
        except json.JSONDecodeError:
            continue
    return "\n".join(texts) if texts else raw


async def run_codex(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    device: str = "local",
    timeout: int = 600,
) -> WorkerResult:
    """Run task with Codex CLI (GPT-5.2, xhigh reasoning).

    Best for: debugging, test writing, recursive call analysis, code review.
    """
    prompt = _build_prompt("codex", task, context_files)
    escaped_prompt = prompt.replace("'", "'\\''")

    if device == "theodolos":
        cwd = working_dir or "~"
        cmd = [
            "ssh", THEODOLOS_HOST,
            f"cd {cwd} && {THEODOLOS_BIN}/codex exec --json -c model={CODEX_MODEL} -c model_reasoning_effort=xhigh -c 'sandbox_permissions=[\"disk-full-read-access\", \"disk-write-cwd\"]' '{escaped_prompt}'"
        ]
        return await _run_command(cmd, Path.cwd(), timeout, "codex", device, _parse_codex_output)
    else:
        codex_path = shutil.which("codex")
        if not codex_path:
            return WorkerResult(success=False, output="", error="Codex CLI not found", backend="codex")

        cwd = Path(working_dir) if working_dir else Path.cwd()
        cmd = [
            codex_path,
            "exec",
            "--json",
            "-c", f"model={CODEX_MODEL}",
            "-c", "model_reasoning_effort=xhigh",
            "-c", 'sandbox_permissions=["disk-full-read-access", "disk-write-cwd"]',
            prompt,
        ]
        return await _run_command(cmd, cwd, timeout, "codex", device, _parse_codex_output)


async def run_kimi(
    task: str,
    device: str = "local",
    timeout: int = 600,
) -> WorkerResult:
    """Run task with Kimi CLI (Kimi K2.5 Thinking).

    Best for: deep internet research, finding documentation, understanding systems.
    No context files - Kimi researches online.
    """
    prompt = _build_prompt("kimi", task, None)
    escaped_prompt = prompt.replace("'", "'\\''")

    if device == "theodolos":
        cmd = [
            "ssh", THEODOLOS_HOST,
            f"{THEODOLOS_BIN}/kimi --thinking -p '{escaped_prompt}' --print --output-format stream-json"
        ]
        return await _run_command(cmd, Path.cwd(), timeout, "kimi", device, _parse_kimi_output)
    else:
        kimi_path = shutil.which("kimi")
        if not kimi_path:
            return WorkerResult(success=False, output="", error="Kimi CLI not found", backend="kimi")

        empty_mcp = Path("/tmp/emrakul-kimi-empty-mcp.json")
        if not empty_mcp.exists():
            empty_mcp.write_text('{"mcpServers":{}}')

        cmd = [
            kimi_path,
            "--thinking",
            "-p", prompt,
            "--print",
            "--output-format", "stream-json",
            "--mcp-config-file", str(empty_mcp),
        ]
        return await _run_command(cmd, Path.cwd(), timeout, "kimi", device, _parse_kimi_output)


async def run_opencode(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    device: str = "local",
    timeout: int = 300,
) -> WorkerResult:
    """Run task with OpenCode CLI (xAI GLM 4.7).

    Best for: quick edits, small fixes, fast turnaround.
    Uses $200/month xAI coding plan.
    """
    prompt = _build_prompt("opencode", task, context_files)
    escaped_prompt = prompt.replace("'", "'\\''")

    if device == "theodolos":
        cwd = working_dir or "~"
        cmd = [
            "ssh", THEODOLOS_HOST,
            f"cd {cwd} && opencode run -m {OPENCODE_MODEL} --format json '{escaped_prompt}'"
        ]
        return await _run_command(cmd, Path.cwd(), timeout, "opencode", device, _parse_opencode_output)
    else:
        opencode_path = shutil.which("opencode")
        if not opencode_path:
            return WorkerResult(success=False, output="", error="OpenCode CLI not found", backend="opencode")

        cwd = Path(working_dir) if working_dir else Path.cwd()
        cmd = [opencode_path, "run", "-m", OPENCODE_MODEL, "--format", "json", prompt]
        return await _run_command(cmd, cwd, timeout, "opencode", device, _parse_opencode_output)


async def run_cursor(
    task: str,
    context_files: Optional[list[str]] = None,
    working_dir: Optional[str] = None,
    device: str = "local",
    timeout: Optional[int] = None,
) -> WorkerResult:
    """Run task with Cursor CLI (Opus 4.5 Thinking).

    Primary implementation worker. $20k credits available.
    Best for: implementation, refactors, complex multi-file changes.
    Note: Base Opus 4.5 is not sufficient - must use Thinking variant.
    """
    prompt = _build_prompt("cursor", task, context_files)
    escaped_prompt = prompt.replace("'", "'\\''")

    if device == "theodolos":
        cwd = working_dir or "~"
        cmd = [
            "ssh", THEODOLOS_HOST,
            f"cd {cwd} && {THEODOLOS_BIN}/cursor-agent --model {CURSOR_MODEL} --print --force --output-format json '{escaped_prompt}'"
        ]
        return await _run_command(cmd, Path.cwd(), timeout, "cursor", device, _parse_cursor_output)
    else:
        cursor_path = shutil.which("cursor")
        if not cursor_path:
            return WorkerResult(success=False, output="", error="Cursor CLI not found", backend="cursor")

        cwd = Path(working_dir) if working_dir else Path.cwd()
        cmd = [
            cursor_path,
            "agent",
            "--model", CURSOR_MODEL,
            "--print",
            "--force",
            "--output-format", "json",
            "--workspace", str(cwd),
            prompt,
        ]
        return await _run_command(cmd, cwd, timeout, "cursor", device, _parse_cursor_output)


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
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                parts.append(f"--- {f} ---\n{content}")

    return "\n\n".join(parts)


async def _run_command(
    cmd: list[str],
    cwd: Path,
    timeout: Optional[int],
    backend: str,
    device: str = "local",
    parser: Optional[callable] = None,
) -> WorkerResult:
    """Execute command and capture output."""
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # If timeout is None, wait indefinitely
        if timeout is None:
            stdout, stderr = await proc.communicate()
        else:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        raw_output = stdout.decode()

        if proc.returncode != 0:
            return WorkerResult(
                success=False,
                output=raw_output,
                error=stderr.decode(),
                backend=backend,
                device=device,
            )

        # Parse output if parser provided
        output = parser(raw_output) if parser else raw_output

        return WorkerResult(
            success=True,
            output=output,
            backend=backend,
            device=device,
        )

    except asyncio.TimeoutError:
        # Kill the process on timeout
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        return WorkerResult(
            success=False,
            output="",
            error=f"Timeout after {timeout}s - process killed",
            backend=backend,
            device=device,
        )
    except Exception as e:
        # Kill the process on error
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        return WorkerResult(
            success=False,
            output="",
            error=str(e),
            backend=backend,
            device=device,
        )
