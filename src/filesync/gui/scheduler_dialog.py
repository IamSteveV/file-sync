"""Backup scheduler configuration dialog."""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
import uuid
from ..scheduler.backup_scheduler import (
    BackupScheduler, ScheduledTask, TaskType, ScheduleFrequency
)


class SchedulerDialog(ctk.CTkToplevel):
    """Dialog for managing backup schedules."""

    def __init__(self, parent, scheduler: BackupScheduler):
        """
        Initialize scheduler dialog.

        Args:
            parent: Parent window
            scheduler: BackupScheduler instance
        """
        super().__init__(parent)

        self.scheduler = scheduler

        self.title("Backup Scheduler")
        self.geometry("900x700")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_tasks()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="gray20")
        header_frame.pack(fill="x")

        ctk.CTkLabel(
            header_frame,
            text="⏰ Backup Scheduler",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            info_frame,
            text="Schedule automated backup, validation, and maintenance tasks",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w")

        # Main content area
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        # Add task button
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="+ Add Task",
            command=self._add_task,
            width=140,
            height=35
        ).pack(side="left")

        # Tasks list
        self.tasks_frame = ctk.CTkScrollableFrame(content_frame)
        self.tasks_frame.grid(row=1, column=0, sticky="nsew")

        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=120,
            height=40
        ).pack(pady=20)

    def _load_tasks(self):
        """Load and display all tasks."""
        # Clear existing widgets
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        tasks = self.scheduler.get_all_tasks()

        if not tasks:
            ctk.CTkLabel(
                self.tasks_frame,
                text="No scheduled tasks configured",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            ).pack(pady=40)
        else:
            for task in tasks:
                self._add_task_card(task)

    def _add_task_card(self, task: ScheduledTask):
        """Add a task card to the list."""
        card = ctk.CTkFrame(self.tasks_frame, fg_color="gray25")
        card.pack(fill="x", pady=8, padx=5)

        # Main content area
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)

        # Header row
        header_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_row.pack(fill="x")

        # Task type
        task_type_label = ctk.CTkLabel(
            header_row,
            text=task.task_type.value.title(),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        task_type_label.pack(side="left")

        # Enabled badge
        if task.enabled:
            enabled_badge = ctk.CTkLabel(
                header_row,
                text="ENABLED",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="green",
                corner_radius=5,
                padx=8,
                pady=3
            )
            enabled_badge.pack(side="left", padx=10)
        else:
            disabled_badge = ctk.CTkLabel(
                header_row,
                text="DISABLED",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="gray40",
                corner_radius=5,
                padx=8,
                pady=3
            )
            disabled_badge.pack(side="left", padx=10)

        # Schedule info
        schedule_text = self._format_schedule(task)
        schedule_label = ctk.CTkLabel(
            content_frame,
            text=schedule_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        schedule_label.pack(anchor="w", pady=(8, 0))

        # Next run info
        if task.next_run and task.enabled:
            from datetime import datetime
            next_run_dt = datetime.fromtimestamp(task.next_run)
            next_run_text = f"Next run: {next_run_dt.strftime('%Y-%m-%d %H:%M:%S')}"

            next_run_label = ctk.CTkLabel(
                content_frame,
                text=next_run_text,
                font=ctk.CTkFont(size=11),
                text_color="lightblue",
                anchor="w"
            )
            next_run_label.pack(anchor="w", pady=(5, 0))

        # Buttons
        btn_container = ctk.CTkFrame(card, fg_color="transparent")
        btn_container.pack(side="right", padx=15)

        # Enable/Disable toggle
        if task.enabled:
            toggle_btn = ctk.CTkButton(
                btn_container,
                text="Disable",
                command=lambda: self._toggle_task(task.task_id, False),
                width=80,
                height=30,
                fg_color="gray40",
                hover_color="gray50"
            )
        else:
            toggle_btn = ctk.CTkButton(
                btn_container,
                text="Enable",
                command=lambda: self._toggle_task(task.task_id, True),
                width=80,
                height=30,
                fg_color="green",
                hover_color="darkgreen"
            )
        toggle_btn.pack(pady=5)

        # Edit button
        edit_btn = ctk.CTkButton(
            btn_container,
            text="Edit",
            command=lambda: self._edit_task(task),
            width=80,
            height=30,
            fg_color="blue",
            hover_color="darkblue"
        )
        edit_btn.pack(pady=5)

        # Delete button
        delete_btn = ctk.CTkButton(
            btn_container,
            text="Delete",
            command=lambda: self._delete_task(task.task_id),
            width=80,
            height=30,
            fg_color="red",
            hover_color="darkred"
        )
        delete_btn.pack(pady=5)

    def _format_schedule(self, task: ScheduledTask) -> str:
        """Format task schedule as readable string."""
        if task.frequency == ScheduleFrequency.HOURLY:
            return f"Runs hourly at :{task.minute:02d}"

        elif task.frequency == ScheduleFrequency.DAILY:
            return f"Runs daily at {task.hour:02d}:{task.minute:02d}"

        elif task.frequency == ScheduleFrequency.WEEKLY:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = days[task.day_of_week] if task.day_of_week is not None else "Unknown"
            return f"Runs weekly on {day_name} at {task.hour:02d}:{task.minute:02d}"

        elif task.frequency == ScheduleFrequency.MONTHLY:
            return f"Runs monthly on day {task.day_of_month} at {task.hour:02d}:{task.minute:02d}"

        elif task.frequency == ScheduleFrequency.CUSTOM:
            return f"Runs every {task.custom_interval_hours} hours"

        return "Unknown schedule"

    def _add_task(self):
        """Add a new task."""
        dialog = TaskEditorDialog(self, None)
        self.wait_window(dialog)

        if hasattr(dialog, 'task') and dialog.task:
            self.scheduler.add_task(dialog.task)
            self._load_tasks()

    def _edit_task(self, task: ScheduledTask):
        """Edit an existing task."""
        dialog = TaskEditorDialog(self, task)
        self.wait_window(dialog)

        if hasattr(dialog, 'task') and dialog.task:
            self.scheduler.add_task(dialog.task)  # This will update existing
            self._load_tasks()

    def _delete_task(self, task_id: str):
        """Delete a task."""
        result = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this task?",
            parent=self
        )

        if result:
            self.scheduler.remove_task(task_id)
            self._load_tasks()

    def _toggle_task(self, task_id: str, enable: bool):
        """Enable or disable a task."""
        if enable:
            self.scheduler.enable_task(task_id)
        else:
            self.scheduler.disable_task(task_id)

        self._load_tasks()


class TaskEditorDialog(ctk.CTkToplevel):
    """Dialog for creating/editing a scheduled task."""

    def __init__(self, parent, task: Optional[ScheduledTask]):
        """
        Initialize task editor.

        Args:
            parent: Parent window
            task: Task to edit (None for new task)
        """
        super().__init__(parent)

        self.editing_task = task
        self.task = None

        self.title("Edit Task" if task else "Add Task")
        self.geometry("500x650")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if task:
            self._load_task_data(task)

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        title = "Edit Scheduled Task" if self.editing_task else "Add Scheduled Task"
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 30))

        # Form
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Task type
        ctk.CTkLabel(
            form_frame,
            text="Task Type:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        self.task_type_var = ctk.StringVar(value=TaskType.VALIDATION.value)
        task_types = [t.value.title() for t in TaskType]

        for task_type in TaskType:
            ctk.CTkRadioButton(
                form_frame,
                text=f"{task_type.value.title()} - {self._get_task_description(task_type)}",
                variable=self.task_type_var,
                value=task_type.value
            ).pack(anchor="w", pady=3, padx=10)

        # Frequency
        ctk.CTkLabel(
            form_frame,
            text="Frequency:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        self.frequency_var = ctk.StringVar(value=ScheduleFrequency.DAILY.value)

        for freq in ScheduleFrequency:
            ctk.CTkRadioButton(
                form_frame,
                text=freq.value.title(),
                variable=self.frequency_var,
                value=freq.value,
                command=self._on_frequency_changed
            ).pack(anchor="w", pady=3, padx=10)

        # Schedule details frame (changes based on frequency)
        self.schedule_details_frame = ctk.CTkFrame(form_frame)
        self.schedule_details_frame.pack(fill="x", pady=(20, 0))

        self._create_schedule_details()

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray40",
            hover_color="gray50",
            width=120,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save_task,
            width=120,
            height=40
        ).pack(side="left", padx=10)

    def _get_task_description(self, task_type: TaskType) -> str:
        """Get description for task type."""
        descriptions = {
            TaskType.VALIDATION: "Check file redundancy requirements",
            TaskType.VERIFICATION: "Verify file integrity across providers",
            TaskType.LIFECYCLE: "Apply lifecycle policies (tier promotion/demotion)",
            TaskType.SYNC: "Synchronize files across providers",
            TaskType.BACKUP: "Perform full backup operation",
        }
        return descriptions.get(task_type, "")

    def _on_frequency_changed(self, *args):
        """Handle frequency change."""
        self._create_schedule_details()

    def _create_schedule_details(self):
        """Create schedule detail widgets based on frequency."""
        # Clear existing widgets
        for widget in self.schedule_details_frame.winfo_children():
            widget.destroy()

        frequency = ScheduleFrequency(self.frequency_var.get())

        ctk.CTkLabel(
            self.schedule_details_frame,
            text="Schedule Details:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        if frequency == ScheduleFrequency.HOURLY:
            self._create_hourly_schedule()
        elif frequency == ScheduleFrequency.DAILY:
            self._create_daily_schedule()
        elif frequency == ScheduleFrequency.WEEKLY:
            self._create_weekly_schedule()
        elif frequency == ScheduleFrequency.MONTHLY:
            self._create_monthly_schedule()
        elif frequency == ScheduleFrequency.CUSTOM:
            self._create_custom_schedule()

    def _create_hourly_schedule(self):
        """Create hourly schedule controls."""
        frame = ctk.CTkFrame(self.schedule_details_frame, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            frame,
            text="Minute:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        self.minute_var = ctk.StringVar(value="0")
        ctk.CTkEntry(
            frame,
            textvariable=self.minute_var,
            width=60,
            height=30
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            frame,
            text="(0-59)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left")

    def _create_daily_schedule(self):
        """Create daily schedule controls."""
        frame = ctk.CTkFrame(self.schedule_details_frame, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            frame,
            text="Time:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        self.hour_var = ctk.StringVar(value="0")
        ctk.CTkEntry(
            frame,
            textvariable=self.hour_var,
            width=60,
            height=30,
            placeholder_text="HH"
        ).pack(side="left", padx=10)

        ctk.CTkLabel(frame, text=":").pack(side="left")

        self.minute_var = ctk.StringVar(value="0")
        ctk.CTkEntry(
            frame,
            textvariable=self.minute_var,
            width=60,
            height=30,
            placeholder_text="MM"
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            frame,
            text="(24-hour format)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left", padx=10)

    def _create_weekly_schedule(self):
        """Create weekly schedule controls."""
        # Day selection
        day_frame = ctk.CTkFrame(self.schedule_details_frame, fg_color="transparent")
        day_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            day_frame,
            text="Day of Week:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(0, 5))

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.day_of_week_var = ctk.StringVar(value="0")

        ctk.CTkOptionMenu(
            day_frame,
            variable=self.day_of_week_var,
            values=[f"{i} - {day}" for i, day in enumerate(days)],
            width=200,
            height=30
        ).pack(anchor="w")

        # Time selection
        self._create_daily_schedule()

    def _create_monthly_schedule(self):
        """Create monthly schedule controls."""
        # Day of month selection
        day_frame = ctk.CTkFrame(self.schedule_details_frame, fg_color="transparent")
        day_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            day_frame,
            text="Day of Month:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        self.day_of_month_var = ctk.StringVar(value="1")
        ctk.CTkEntry(
            day_frame,
            textvariable=self.day_of_month_var,
            width=60,
            height=30
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            day_frame,
            text="(1-31)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left")

        # Time selection
        self._create_daily_schedule()

    def _create_custom_schedule(self):
        """Create custom schedule controls."""
        frame = ctk.CTkFrame(self.schedule_details_frame, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            frame,
            text="Run every:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        self.custom_hours_var = ctk.StringVar(value="24")
        ctk.CTkEntry(
            frame,
            textvariable=self.custom_hours_var,
            width=80,
            height=30
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            frame,
            text="hours",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

    def _load_task_data(self, task: ScheduledTask):
        """Load task data into form."""
        self.task_type_var.set(task.task_type.value)
        self.frequency_var.set(task.frequency.value)

        self._create_schedule_details()

        # Set schedule details based on frequency
        if task.frequency == ScheduleFrequency.HOURLY:
            self.minute_var.set(str(task.minute))

        elif task.frequency == ScheduleFrequency.DAILY:
            self.hour_var.set(str(task.hour))
            self.minute_var.set(str(task.minute))

        elif task.frequency == ScheduleFrequency.WEEKLY:
            if task.day_of_week is not None:
                self.day_of_week_var.set(f"{task.day_of_week} - {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][task.day_of_week]}")
            self.hour_var.set(str(task.hour))
            self.minute_var.set(str(task.minute))

        elif task.frequency == ScheduleFrequency.MONTHLY:
            if task.day_of_month is not None:
                self.day_of_month_var.set(str(task.day_of_month))
            self.hour_var.set(str(task.hour))
            self.minute_var.set(str(task.minute))

        elif task.frequency == ScheduleFrequency.CUSTOM:
            if task.custom_interval_hours:
                self.custom_hours_var.set(str(task.custom_interval_hours))

    def _save_task(self):
        """Save the task."""
        try:
            # Get task ID (use existing or generate new)
            task_id = self.editing_task.task_id if self.editing_task else str(uuid.uuid4())

            # Get basic fields
            task_type = TaskType(self.task_type_var.get())
            frequency = ScheduleFrequency(self.frequency_var.get())

            # Build task based on frequency
            task_data = {
                'task_id': task_id,
                'task_type': task_type,
                'frequency': frequency,
                'enabled': True if not self.editing_task else self.editing_task.enabled,
            }

            if frequency == ScheduleFrequency.HOURLY:
                task_data['minute'] = int(self.minute_var.get())

            elif frequency == ScheduleFrequency.DAILY:
                task_data['hour'] = int(self.hour_var.get())
                task_data['minute'] = int(self.minute_var.get())

            elif frequency == ScheduleFrequency.WEEKLY:
                day_value = self.day_of_week_var.get().split(' - ')[0]
                task_data['day_of_week'] = int(day_value)
                task_data['hour'] = int(self.hour_var.get())
                task_data['minute'] = int(self.minute_var.get())

            elif frequency == ScheduleFrequency.MONTHLY:
                task_data['day_of_month'] = int(self.day_of_month_var.get())
                task_data['hour'] = int(self.hour_var.get())
                task_data['minute'] = int(self.minute_var.get())

            elif frequency == ScheduleFrequency.CUSTOM:
                task_data['custom_interval_hours'] = int(self.custom_hours_var.get())

            self.task = ScheduledTask(**task_data)
            self.destroy()

        except ValueError as e:
            messagebox.showerror(
                "Invalid Input",
                f"Please check your inputs:\n{str(e)}",
                parent=self
            )
