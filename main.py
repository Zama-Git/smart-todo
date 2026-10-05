import tkinter as tk
from datetime import datetime
from typing import List, Optional

import customtkinter as ctk

from models import Task
from storage import load_tasks, save_tasks
from reminders import ReminderService

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str, delay: int = 400) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id: Optional[str] = None
        self._tip: Optional[tk.Toplevel] = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            background="#111827",
            foreground="#e5e7eb",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padx=10,
            pady=6,
        )
        label.pack()

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class SmartTodoApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Smart Todo")
        self.geometry("740x740")
        self.minsize(720, 560)

        self.tasks: List[Task] = load_tasks()
        self.current_filter: str = "all"

        self._build_ui()
        self._render_tasks()

        self.reminders = ReminderService(
            get_tasks=lambda: self.tasks,
            save_tasks=save_tasks,
            on_remind=self._on_remind_from_thread,
        )
        self.reminders.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkLabel(
            self, text="Smart Todo",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        self.title_entry = ctk.CTkEntry(form, placeholder_text="Cosa devi fare?")
        self.title_entry.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="ew")
        self.title_entry.bind("<Return>", lambda _e: self._add_task())

        add_btn = ctk.CTkButton(form, text="Aggiungi", width=100, command=self._add_task)
        add_btn.grid(row=0, column=1, pady=(0, 8))

        due_row = ctk.CTkFrame(form, fg_color="transparent")
        due_row.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        now = datetime.now()

        ctk.CTkLabel(due_row, text="Scadenza:").grid(row=0, column=0, padx=(0, 8))

        self.day_var = ctk.StringVar(value=f"{now.day:02d}")
        ctk.CTkOptionMenu(
            due_row, values=[f"{d:02d}" for d in range(1, 32)],
            variable=self.day_var, width=62,
        ).grid(row=0, column=1, padx=2)

        self.month_var = ctk.StringVar(value=f"{now.month:02d}")
        ctk.CTkOptionMenu(
            due_row, values=[f"{m:02d}" for m in range(1, 13)],
            variable=self.month_var, width=62,
        ).grid(row=0, column=2, padx=2)

        self.year_var = ctk.StringVar(value=str(now.year))
        ctk.CTkOptionMenu(
            due_row, values=[str(y) for y in range(now.year, now.year + 6)],
            variable=self.year_var, width=82,
        ).grid(row=0, column=3, padx=2)

        ctk.CTkLabel(due_row, text="·").grid(row=0, column=4, padx=4)

        self.hour_var = ctk.StringVar(value=f"{now.hour:02d}")
        ctk.CTkOptionMenu(
            due_row, values=[f"{h:02d}" for h in range(24)],
            variable=self.hour_var, width=62,
        ).grid(row=0, column=5, padx=2)

        ctk.CTkLabel(due_row, text=":").grid(row=0, column=6)

        self.minute_var = ctk.StringVar(value=f"{(now.minute // 5) * 5:02d}")
        ctk.CTkOptionMenu(
            due_row, values=[f"{m:02d}" for m in range(0, 60, 5)],
            variable=self.minute_var, width=62,
        ).grid(row=0, column=7, padx=2)

        self.due_enabled = ctk.BooleanVar(value=True)
        toggle = ctk.CTkCheckBox(
            due_row,
            text="attiva",
            variable=self.due_enabled,
            checkbox_width=18,
            checkbox_height=18,
        )
        toggle.grid(row=0, column=8, padx=(14, 0))

        Tooltip(
            toggle,
            "Se attiva, la task avrà una scadenza.\n"
            "Quando arriva il momento, ricevi una notifica\n"
            "di sistema (una sola volta).\n\n"
            "Se disattiva, la task non ti ricorderà nulla.",
        )

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Le tue attività")
        self.list_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        for label, value in (("Tutte", "all"), ("Attive", "active"), ("Completate", "done")):
            ctk.CTkButton(
                filters, text=label, width=110,
                command=lambda v=value: self._set_filter(v),
            ).pack(side="left", padx=(0, 8))

        self.counter_label = ctk.CTkLabel(filters, text="")
        self.counter_label.pack(side="right")

    def _add_task(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            return

        due_str: Optional[str] = None
        if self.due_enabled.get():
            try:
                due = datetime(
                    int(self.year_var.get()),
                    int(self.month_var.get()),
                    int(self.day_var.get()),
                    int(self.hour_var.get()),
                    int(self.minute_var.get()),
                )
                due_str = due.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                return

        self.tasks.insert(0, Task(title=title, due_at=due_str))
        self.title_entry.delete(0, "end")
        self._save_and_refresh()

    def _toggle_task(self, task: Task) -> None:
        task.done = not task.done
        self._save_and_refresh()

    def _delete_task(self, task: Task) -> None:
        self.tasks = [t for t in self.tasks if t.id != task.id]
        self._save_and_refresh()

    def _set_filter(self, value: str) -> None:
        self.current_filter = value
        self._render_tasks()

    def _save_and_refresh(self) -> None:
        save_tasks(self.tasks)
        self._render_tasks()

    def _render_tasks(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        visible = [t for t in self.tasks if self._matches_filter(t)]

        if not visible:
            ctk.CTkLabel(
                self.list_frame, text="Nessuna attività.",
                text_color="gray",
            ).grid(row=0, column=0, pady=20)
        else:
            for i, task in enumerate(visible):
                self._render_row(i, task)

        remaining = sum(1 for t in self.tasks if not t.done)
        self.counter_label.configure(
            text=f"{remaining} rimaste" if remaining != 1 else "1 rimasta"
        )

    def _matches_filter(self, task: Task) -> bool:
        if self.current_filter == "active":
            return not task.done
        if self.current_filter == "done":
            return task.done
        return True

    def _render_row(self, index: int, task: Task) -> None:
        row = ctk.CTkFrame(self.list_frame)
        row.grid(row=index, column=0, sticky="ew", pady=4)
        row.grid_columnconfigure(1, weight=1)

        var = ctk.BooleanVar(value=task.done)
        ctk.CTkCheckBox(
            row, text="", width=24, variable=var,
            command=lambda t=task: self._toggle_task(t),
        ).grid(row=0, column=0, padx=(10, 8), pady=10)

        title = ctk.CTkLabel(
            row, text=task.title, anchor="w",
            font=ctk.CTkFont(size=14, overstrike=task.done),
        )
        title.grid(row=0, column=1, sticky="ew")

        if task.due_at:
            due_text = task.due_at
            color = "gray"
            try:
                due_dt = datetime.strptime(task.due_at, "%Y-%m-%d %H:%M")
                if due_dt <= datetime.now() and not task.done:
                    color = "#ff6b6b"
                    due_text = f"⚠ {due_text}"
            except ValueError:
                pass
            ctk.CTkLabel(
                row, text=due_text, text_color=color,
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=2, padx=10)

        ctk.CTkButton(
            row, text="✕", width=32,
            fg_color="transparent", hover_color="#7f1d1d",
            command=lambda t=task: self._delete_task(t),
        ).grid(row=0, column=3, padx=(0, 8))

    def _on_remind_from_thread(self, task: Task) -> None:
        self.after(0, self._render_tasks)

    def _on_close(self) -> None:
        self.reminders.stop()
        self.destroy()


if __name__ == "__main__":
    app = SmartTodoApp()
    app.mainloop()