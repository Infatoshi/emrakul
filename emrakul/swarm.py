"""Emrakul Swarm - Task queue with backend-specific routing.

Unlike AlphaHENG's fallback chain, Emrakul routes tasks to explicitly
assigned backends:
- codex: debugging + tests
- kimi: research
- cursor: implementation
- opencode: quick edits

Tasks are submitted via YAML, queued by priority, and dispatched to
the specified backend on the specified device.
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

from emrakul.workers import run_codex, run_cursor, run_kimi, run_opencode


class Priority(Enum):
    P0 = 0  # Critical - run first
    P1 = 1  # High
    P2 = 2  # Normal (default)
    P3 = 3  # Low - run last

    @classmethod
    def from_str(cls, s: str) -> "Priority":
        return cls[s.upper()]


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """A single task to execute."""

    id: str
    name: str
    prompt: str
    backend: str  # codex, kimi, cursor, opencode
    priority: Priority = Priority.P2
    device: str = "local"  # local or theodolos
    verify: Optional[str] = None  # Verification command
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context_files: list[str] = field(default_factory=list)
    working_dir: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        """Create task from YAML dict."""
        # Generate stable ID from name + prompt
        id_input = f"{d['name']}:{d['prompt'][:100]}"
        task_id = hashlib.sha256(id_input.encode()).hexdigest()[:12]

        return cls(
            id=task_id,
            name=d["name"],
            prompt=d["prompt"],
            backend=d.get("backend", "cursor"),
            priority=Priority.from_str(d.get("priority", "P2")),
            device=d.get("device", "local"),
            verify=d.get("verify"),
            dependencies=d.get("dependencies", []),
            context_files=d.get("context_files", []),
            working_dir=d.get("working_dir"),
        )


class Swarm:
    """Task queue with priority scheduling and backend routing."""

    def __init__(self):
        # Priority queues: P0, P1, P2, P3
        self.queues: dict[Priority, list[Task]] = {p: [] for p in Priority}
        self.tasks: dict[str, Task] = {}  # All tasks by ID
        self.tasks_by_name: dict[str, Task] = {}  # Tasks by name for deps
        self.running = False
        self.workers: list[asyncio.Task] = []
        self.max_concurrent = 10  # Max concurrent tasks

    def add_task(self, task: Task) -> None:
        """Add task to queue."""
        self.tasks[task.id] = task
        self.tasks_by_name[task.name] = task
        self.queues[task.priority].append(task)

    def add_tasks_from_yaml(self, yaml_path: str) -> list[Task]:
        """Load and add tasks from YAML file."""
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Tasks file not found: {yaml_path}")

        data = yaml.safe_load(path.read_text())
        tasks_data = data.get("tasks", [])

        added = []
        for t in tasks_data:
            task = Task.from_dict(t)
            self.add_task(task)
            added.append(task)

        return added

    def add_tasks_from_string(self, yaml_content: str) -> list[Task]:
        """Load and add tasks from YAML string."""
        data = yaml.safe_load(yaml_content)
        tasks_data = data.get("tasks", [])

        added = []
        for t in tasks_data:
            task = Task.from_dict(t)
            self.add_task(task)
            added.append(task)

        return added

    def get_next_task(self) -> Optional[Task]:
        """Get highest priority task that's ready to run."""
        for priority in Priority:
            queue = self.queues[priority]
            for i, task in enumerate(queue):
                if task.status != TaskStatus.PENDING:
                    continue
                # Check dependencies
                if self._deps_satisfied(task):
                    queue.pop(i)
                    return task
        return None

    def _deps_satisfied(self, task: Task) -> bool:
        """Check if all dependencies are completed."""
        for dep_name in task.dependencies:
            dep = self.tasks_by_name.get(dep_name)
            if not dep or dep.status != TaskStatus.COMPLETED:
                return False
        return True

    async def execute_task(self, task: Task) -> None:
        """Execute a single task on its assigned backend."""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        # Backend-specific timeouts (seconds, None = no timeout)
        timeouts = {
            "cursor": None,  # No timeout - complex work takes as long as needed
            "codex": 600,    # 10 min - debugging/tests
            "kimi": 300,     # 5 min - research
            "opencode": 180, # 3 min - quick edits
        }
        timeout = timeouts.get(task.backend, 600)

        try:
            # Route to correct backend
            if task.backend == "codex":
                result = await run_codex(
                    task.prompt, task.context_files, task.working_dir, task.device, timeout=timeout
                )
            elif task.backend == "kimi":
                result = await run_kimi(task.prompt, task.device, timeout=timeout)
            elif task.backend == "cursor":
                result = await run_cursor(
                    task.prompt, task.context_files, task.working_dir, task.device, timeout=timeout
                )
            elif task.backend == "opencode":
                result = await run_opencode(
                    task.prompt, task.context_files, task.working_dir, task.device, timeout=timeout
                )
            else:
                raise ValueError(f"Unknown backend: {task.backend}")

            if not result.success:
                raise RuntimeError(result.error or "Task execution failed")

            # Run verification if specified
            if task.verify:
                verified = await self._verify(task)
                if not verified:
                    raise RuntimeError("Verification failed")

            task.status = TaskStatus.COMPLETED
            task.result = {"output": result.output, "backend": result.backend}
            task.completed_at = datetime.now()

        except Exception as e:
            task.error = str(e)
            task.retries += 1

            if task.retries < task.max_retries:
                # Requeue for retry
                task.status = TaskStatus.PENDING
                self.queues[task.priority].append(task)
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()

    async def _verify(self, task: Task) -> bool:
        """Run verification command."""
        if not task.verify:
            return True

        try:
            cwd = Path(task.working_dir) if task.working_dir else Path.cwd()
            proc = await asyncio.create_subprocess_shell(
                task.verify,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            return proc.returncode == 0
        except Exception:
            return False

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker coroutine that pulls and executes tasks."""
        while self.running:
            task = self.get_next_task()
            if task:
                await self.execute_task(task)
            else:
                await asyncio.sleep(0.5)  # No tasks, wait

    async def start(self, num_workers: int = 5) -> None:
        """Start the swarm with N workers."""
        if self.running:
            return

        self.running = True
        self.max_concurrent = num_workers

        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker)

    async def stop(self) -> None:
        """Stop the swarm."""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        self.workers = []

    def status(self) -> dict[str, Any]:
        """Get swarm status."""
        pending = sum(
            1
            for t in self.tasks.values()
            if t.status == TaskStatus.PENDING
        )
        in_progress = sum(
            1
            for t in self.tasks.values()
            if t.status == TaskStatus.IN_PROGRESS
        )
        completed = sum(
            1
            for t in self.tasks.values()
            if t.status == TaskStatus.COMPLETED
        )
        failed = sum(
            1
            for t in self.tasks.values()
            if t.status == TaskStatus.FAILED
        )

        # Count by backend
        by_backend: dict[str, dict[str, int]] = {}
        for task in self.tasks.values():
            if task.backend not in by_backend:
                by_backend[task.backend] = {"pending": 0, "completed": 0, "failed": 0}
            if task.status == TaskStatus.PENDING:
                by_backend[task.backend]["pending"] += 1
            elif task.status == TaskStatus.COMPLETED:
                by_backend[task.backend]["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                by_backend[task.backend]["failed"] += 1

        return {
            "running": self.running,
            "workers": len(self.workers),
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
            "total": len(self.tasks),
            "by_backend": by_backend,
        }

    def results(self, include_pending: bool = False) -> list[dict[str, Any]]:
        """Get task results."""
        results = []
        for task in self.tasks.values():
            if not include_pending and task.status == TaskStatus.PENDING:
                continue

            results.append({
                "id": task.id,
                "name": task.name,
                "backend": task.backend,
                "device": task.device,
                "status": task.status.value,
                "result": task.result,
                "error": task.error,
                "retries": task.retries,
            })

        return results

    def clear(self) -> None:
        """Clear all tasks."""
        self.queues = {p: [] for p in Priority}
        self.tasks = {}
        self.tasks_by_name = {}


# Global swarm instance
_swarm: Optional[Swarm] = None


def get_swarm() -> Swarm:
    """Get or create global swarm instance."""
    global _swarm
    if _swarm is None:
        _swarm = Swarm()
    return _swarm
