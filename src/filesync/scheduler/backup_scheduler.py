"""Backup scheduler for automated tasks."""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class TaskType(Enum):
    """Types of scheduled tasks."""
    VALIDATION = "validation"
    VERIFICATION = "verification"
    LIFECYCLE = "lifecycle"
    SYNC = "sync"
    BACKUP = "backup"


class ScheduleFrequency(Enum):
    """Schedule frequency options."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    task_id: str
    task_type: TaskType
    frequency: ScheduleFrequency
    enabled: bool
    last_run: Optional[float] = None
    next_run: Optional[float] = None

    # For custom schedules
    custom_interval_hours: Optional[int] = None

    # For weekly schedules
    day_of_week: Optional[int] = None  # 0-6 (Monday-Sunday)

    # For monthly schedules
    day_of_month: Optional[int] = None  # 1-31

    # Time of day (for daily, weekly, monthly)
    hour: int = 0
    minute: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['task_type'] = self.task_type.value
        result['frequency'] = self.frequency.value
        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ScheduledTask':
        """Create from dictionary."""
        data['task_type'] = TaskType(data['task_type'])
        data['frequency'] = ScheduleFrequency(data['frequency'])
        return ScheduledTask(**data)


class BackupScheduler:
    """Manages scheduled backup and maintenance tasks."""

    def __init__(self, config_path: Path):
        """
        Initialize scheduler.

        Args:
            config_path: Path to scheduler configuration file
        """
        self.config_path = config_path
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[TaskType, Callable] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None

        self._load_config()

    def _load_config(self):
        """Load scheduler configuration."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                self.tasks = {
                    task_id: ScheduledTask.from_dict(task_data)
                    for task_id, task_data in data.get('tasks', {}).items()
                }
            except Exception as e:
                print(f"Error loading scheduler config: {e}")
                self.tasks = {}

    def _save_config(self):
        """Save scheduler configuration."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'tasks': {
                    task_id: task.to_dict()
                    for task_id, task in self.tasks.items()
                }
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving scheduler config: {e}")

    def register_handler(self, task_type: TaskType, handler: Callable):
        """
        Register a handler for a task type.

        Args:
            task_type: Type of task
            handler: Function to call when task runs
        """
        self.task_handlers[task_type] = handler

    def add_task(self, task: ScheduledTask) -> str:
        """
        Add a scheduled task.

        Args:
            task: Task to add

        Returns:
            Task ID
        """
        self.tasks[task.task_id] = task
        self._calculate_next_run(task)
        self._save_config()
        return task.task_id

    def remove_task(self, task_id: str):
        """Remove a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_config()

    def enable_task(self, task_id: str):
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._calculate_next_run(self.tasks[task_id])
            self._save_config()

    def disable_task(self, task_id: str):
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_config()

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all tasks."""
        return list(self.tasks.values())

    def start(self):
        """Start the scheduler."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _run(self):
        """Main scheduler loop."""
        while self.running:
            now = time.time()

            for task in self.tasks.values():
                if not task.enabled:
                    continue

                if task.next_run is None:
                    self._calculate_next_run(task)

                if task.next_run and now >= task.next_run:
                    self._execute_task(task)

            # Check every minute
            time.sleep(60)

    def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        print(f"Executing scheduled task: {task.task_id} ({task.task_type.value})")

        try:
            # Get handler for this task type
            handler = self.task_handlers.get(task.task_type)

            if handler:
                handler()
            else:
                print(f"No handler registered for task type: {task.task_type.value}")

            # Update last run time
            task.last_run = time.time()

            # Calculate next run
            self._calculate_next_run(task)

            self._save_config()

        except Exception as e:
            print(f"Error executing task {task.task_id}: {e}")

    def _calculate_next_run(self, task: ScheduledTask):
        """Calculate next run time for a task."""
        now = datetime.now()

        if task.frequency == ScheduleFrequency.HOURLY:
            next_run = now + timedelta(hours=1)
            next_run = next_run.replace(minute=task.minute, second=0, microsecond=0)

        elif task.frequency == ScheduleFrequency.DAILY:
            next_run = now + timedelta(days=1)
            next_run = next_run.replace(hour=task.hour, minute=task.minute, second=0, microsecond=0)

            # If the time hasn't passed today, use today
            target_time = now.replace(hour=task.hour, minute=task.minute, second=0, microsecond=0)
            if target_time > now:
                next_run = target_time

        elif task.frequency == ScheduleFrequency.WEEKLY:
            # Calculate next occurrence of the target day
            days_ahead = task.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=task.hour, minute=task.minute, second=0, microsecond=0)

        elif task.frequency == ScheduleFrequency.MONTHLY:
            # Calculate next occurrence of the target day of month
            next_run = now.replace(day=task.day_of_month, hour=task.hour, minute=task.minute, second=0, microsecond=0)

            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)

        elif task.frequency == ScheduleFrequency.CUSTOM:
            if task.custom_interval_hours:
                next_run = now + timedelta(hours=task.custom_interval_hours)
            else:
                next_run = now + timedelta(hours=24)  # Default to daily

        else:
            next_run = now + timedelta(days=1)

        task.next_run = next_run.timestamp()

    def get_next_runs(self) -> List[Dict[str, Any]]:
        """Get next run times for all enabled tasks."""
        results = []

        for task in self.tasks.values():
            if not task.enabled:
                continue

            if task.next_run:
                next_run_dt = datetime.fromtimestamp(task.next_run)

                results.append({
                    'task_id': task.task_id,
                    'task_type': task.task_type.value,
                    'next_run': task.next_run,
                    'next_run_str': next_run_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'time_until': self._format_time_until(task.next_run)
                })

        # Sort by next run time
        results.sort(key=lambda x: x['next_run'])

        return results

    def _format_time_until(self, timestamp: float) -> str:
        """Format time until a timestamp."""
        now = time.time()
        delta = timestamp - now

        if delta < 0:
            return "Overdue"

        if delta < 60:
            return "Less than 1 minute"
        elif delta < 3600:
            minutes = int(delta / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif delta < 86400:
            hours = int(delta / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = int(delta / 86400)
            return f"{days} day{'s' if days != 1 else ''}"


def create_default_tasks() -> List[ScheduledTask]:
    """Create default scheduled tasks."""
    import uuid

    return [
        ScheduledTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.VALIDATION,
            frequency=ScheduleFrequency.DAILY,
            enabled=True,
            hour=2,  # 2 AM
            minute=0
        ),
        ScheduledTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.VERIFICATION,
            frequency=ScheduleFrequency.WEEKLY,
            enabled=True,
            day_of_week=0,  # Monday
            hour=3,
            minute=0
        ),
        ScheduledTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.LIFECYCLE,
            frequency=ScheduleFrequency.DAILY,
            enabled=True,
            hour=1,
            minute=0
        ),
    ]
