"""Emrakul CLI - Manual worker invocation and status checks."""

import argparse
import asyncio
import sys

from emrakul.workers import run_codex, run_cursor, run_kimi, run_opencode


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

    # serve subcommand
    subparsers.add_parser("serve", help="Run the MCP server")

    args = parser.parse_args()

    if args.command == "delegate":
        result = asyncio.run(_delegate(args))
        if result.success:
            print(f"[{result.backend}@{result.device}]")
            print(result.output)
        else:
            print(f"[{result.backend}@{result.device}] Error: {result.error}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "serve":
        from emrakul.mcp_server import main as serve_main
        serve_main()


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
