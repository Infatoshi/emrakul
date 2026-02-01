"""Emrakul CLI - Manual worker invocation and status checks."""

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from emrakul.workers import run_codex, run_cursor, run_kimi, run_opencode

# Default output directory for background tasks
OUTPUT_DIR = Path.home() / ".emrakul" / "outputs"


def main():
    parser = argparse.ArgumentParser(
        description="Emrakul - Agent orchestration framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # delegate subcommand
    delegate = subparsers.add_parser("delegate", help="Run a task with a specific worker")
    delegate.add_argument(
        "worker",
        choices=["codex", "kimi", "cursor", "opencode"],
        help="Worker to delegate to",
    )
    delegate.add_argument("task", help="Task description")
    delegate.add_argument(
        "-f", "--files",
        nargs="*",
        help="Context files to include",
    )
    delegate.add_argument(
        "-d", "--dir",
        help="Working directory",
    )
    delegate.add_argument(
        "--device",
        choices=["local", "theodolos"],
        default="local",
        help="Device to run on (default: local)",
    )
    delegate.add_argument(
        "-o", "--output",
        help="Output file path (for background execution)",
    )
    delegate.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    delegate.add_argument(
        "--bg",
        action="store_true",
        help="Background mode: auto-generate output file and exit immediately after starting",
    )

    # serve subcommand
    subparsers.add_parser("serve", help="Run the MCP server")

    # status subcommand - check background task outputs
    status = subparsers.add_parser("status", help="Check status of background tasks")
    status.add_argument(
        "task_id",
        nargs="?",
        help="Task ID to check (or 'all' for all recent)",
    )

    args = parser.parse_args()

    if args.command == "delegate":
        # Determine output path
        output_path = None
        if args.bg or args.output:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            if args.output:
                output_path = Path(args.output)
            else:
                task_id = f"{args.worker}-{uuid.uuid4().hex[:8]}"
                output_path = OUTPUT_DIR / f"{task_id}.json"

            # For --bg mode, print path and return immediately
            # The actual execution happens when not using shell &
            print(json.dumps({
                "status": "started",
                "task_id": output_path.stem,
                "output_file": str(output_path),
                "worker": args.worker,
                "device": args.device,
            }))

            # Write initial status
            output_path.write_text(json.dumps({
                "status": "running",
                "worker": args.worker,
                "device": args.device,
                "task": args.task[:200] + "..." if len(args.task) > 200 else args.task,
                "started_at": datetime.now().isoformat(),
            }, indent=2))

        # Run the task
        result = asyncio.run(_delegate(args))

        # Format output
        output_data = {
            "status": "completed" if result.success else "failed",
            "success": result.success,
            "worker": result.backend,
            "device": result.device,
            "output": result.output,
            "error": result.error,
            "completed_at": datetime.now().isoformat(),
        }

        if output_path:
            output_path.write_text(json.dumps(output_data, indent=2))
            if not args.bg:
                print(f"Output written to: {output_path}")
        elif args.json:
            print(json.dumps(output_data, indent=2))
        else:
            if result.success:
                print(f"[{result.backend}@{result.device}]")
                print(result.output)
            else:
                print(f"[{result.backend}@{result.device}] Error: {result.error}", file=sys.stderr)
                sys.exit(1)

    elif args.command == "serve":
        from emrakul.mcp_server import main as serve_main
        serve_main()

    elif args.command == "status":
        _check_status(args.task_id)


def _check_status(task_id: str | None):
    """Check status of background tasks."""
    if not OUTPUT_DIR.exists():
        print("No background tasks found.")
        return

    if task_id and task_id != "all":
        # Check specific task
        task_file = OUTPUT_DIR / f"{task_id}.json"
        if not task_file.exists():
            print(f"Task not found: {task_id}")
            return
        data = json.loads(task_file.read_text())
        print(json.dumps(data, indent=2))
    else:
        # List recent tasks
        files = sorted(OUTPUT_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:10]
        for f in files:
            try:
                data = json.loads(f.read_text())
                status = data.get("status", "unknown")
                worker = data.get("worker", "?")
                print(f"  {f.stem}: {status} ({worker})")
            except Exception:
                print(f"  {f.stem}: <error reading>")


async def _delegate(args):
    """Run delegation based on worker type."""
    if args.worker == "codex":
        return await run_codex(args.task, args.files, args.dir, args.device)
    elif args.worker == "kimi":
        return await run_kimi(args.task, args.device)
    elif args.worker == "cursor":
        return await run_cursor(args.task, args.files, args.dir, args.device)
    elif args.worker == "opencode":
        return await run_opencode(args.task, args.files, args.dir, args.device)


if __name__ == "__main__":
    main()
