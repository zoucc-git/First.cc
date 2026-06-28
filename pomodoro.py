#!/usr/bin/env python3
"""Pomodoro Timer — A clean desktop productivity timer.

Built with Python + tkinter. Zero external dependencies.
"""

import json
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

SETTINGS_FILE = Path.home() / ".pomodoro_settings.json"

DEFAULT_SETTINGS = {
    "work_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "long_break_interval": 4,
    "always_on_top": False,
}

# ── Session types ────────────────────────────────────────────────────────────

WORK = "work"
SHORT_BREAK = "short_break"
LONG_BREAK = "long_break"

SESSION_LABELS = {
    WORK: "\U0001f345 工作中",
    SHORT_BREAK: "☕ 短休息",
    LONG_BREAK: "\U0001f330 长休息",
}

SESSION_MINUTE_KEY = {
    WORK: "work_minutes",
    SHORT_BREAK: "short_break_minutes",
    LONG_BREAK: "long_break_minutes",
}

# Color theme — sunset palette
COLORS = {
    WORK: "#e0583a",          # sinking sun orange-red
    SHORT_BREAK: "#f0a500",   # golden hour
    LONG_BREAK: "#7b4b8a",    # twilight purple
    "bg": "#fef5e7",          # warm cream
    "fg": "#3d2b1f",          # dark walnut
    "button_bg": "#f5e6d3",   # light tan
    "dot_empty": "#e8d5c4",   # warm beige
    "dot_filled": "#f7931e",  # bright tangerine
}


def load_settings():
    """Load settings from disk, falling back to defaults."""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            stored = json.load(f)
        # Merge with defaults in case new keys were added
        return {**DEFAULT_SETTINGS, **stored}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def _center_window(win, parent=None):
    """Center a toplevel window on its parent, or on screen if parent is None."""
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    if parent is not None:
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
    else:
        pw, ph = win.winfo_screenwidth(), win.winfo_screenheight()
        px = py = 0
    win.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")


def save_settings(settings):
    """Persist settings to disk."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # Silently fail — non-critical


# ── Settings Dialog ──────────────────────────────────────────────────────────

class SettingsDialog(tk.Toplevel):
    """Modal settings popup to customize timer durations."""

    def __init__(self, parent, settings, on_save):
        super().__init__(parent)
        self.settings = dict(settings)
        self.on_save = on_save

        self.title("设置 — Pomodoro")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Build UI
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="自定义时长（分钟）", font=("", 11, "bold")).pack(
            anchor=tk.W, pady=(0, 12)
        )

        self.spin_work = self._add_row(frame, "工作时间:", self.settings["work_minutes"])
        self.spin_short = self._add_row(frame, "短休息:", self.settings["short_break_minutes"])
        self.spin_long = self._add_row(frame, "长休息:", self.settings["long_break_minutes"])
        self.spin_interval = self._add_row(
            frame, "长休息间隔（轮）:", self.settings["long_break_interval"], min_val=1, max_val=10
        )

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(16, 0))
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)

        _center_window(self, parent)

    def _add_row(self, parent, label, initial, min_val=1, max_val=120):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
        spin = ttk.Spinbox(
            row, from_=min_val, to=max_val, width=6, justify=tk.CENTER
        )
        spin.set(str(initial))
        spin.pack(side=tk.RIGHT)
        return spin

    def _save(self):
        try:
            self.settings["work_minutes"] = int(self.spin_work.get())
            self.settings["short_break_minutes"] = int(self.spin_short.get())
            self.settings["long_break_minutes"] = int(self.spin_long.get())
            self.settings["long_break_interval"] = int(self.spin_interval.get())
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数字。")
            return
        save_settings(self.settings)
        self.on_save(self.settings)
        self.destroy()


# ── Main Application ─────────────────────────────────────────────────────────

class PomodoroTimer(tk.Tk):
    """The main Pomodoro timer window."""

    def __init__(self):
        super().__init__()

        # ── State ──
        self.settings = load_settings()
        self.session = WORK              # current session type
        self.remaining_sec = self.settings["work_minutes"] * 60
        self.running = False
        self.paused = False
        self.work_count = 0              # completed work sessions in current cycle
        self._after_id = None            # tkinter after callback id
        self._start_ts = None            # wall-clock time when current tick started

        # ── Window setup ──
        self.title("\U0001f345 Pomodoro")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Apply always-on-top from saved settings
        if self.settings.get("always_on_top", False):
            self.attributes("-topmost", True)

        self._build_ui()
        self._update_display()
        self._center_window()
        self._update_button_states()

    # ── UI construction ──────────────────────────────────────────────────

    def _build_ui(self):
        # Main container
        container = tk.Frame(self, bg=COLORS["bg"], padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Header / session label
        self.lbl_session = tk.Label(
            container,
            text="",
            font=("Microsoft YaHei UI", 12),
            bg=COLORS["bg"],
            fg=COLORS["fg"],
        )
        self.lbl_session.pack(pady=(0, 8))

        # Timer display
        timer_frame = tk.Frame(container, bg=COLORS[WORK], padx=40, pady=24)
        timer_frame.pack(pady=(0, 16))
        self.timer_bg = timer_frame  # save ref to update color

        self.lbl_timer = tk.Label(
            timer_frame,
            text="25:00",
            font=("Consolas", 48, "bold"),
            bg=COLORS[WORK],
            fg="white",
        )
        self.lbl_timer.pack()

        # Progress dots
        self.dots_frame = tk.Frame(container, bg=COLORS["bg"])
        self.dots_frame.pack(pady=(0, 16))
        self.dot_labels = []
        self._build_progress_dots()

        # Control buttons
        btn_frame = tk.Frame(container, bg=COLORS["bg"])
        btn_frame.pack(pady=(0, 12))

        def _btn(text, command, bg, abg):
            """Factory: create a flat control button with consistent styling."""
            btn = tk.Button(
                btn_frame, text=text, font=("Microsoft YaHei UI", 10),
                width=10, command=command, bg=bg, fg="white",
                activebackground=abg, relief=tk.FLAT, cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=4)
            return btn

        self.btn_start = _btn("▶ 开始", self.start_timer, "#c97d42", "#d4945a")
        self.btn_pause = _btn("⏸ 暂停", self.pause_timer, "#e0982a", "#e8a830")
        self.btn_reset = _btn("↺ 重置", self.reset_timer, "#b8a088", "#c4b098")
        self.btn_skip = _btn("⏭ 跳过", self.skip_session, "#a09080", "#b0a090")

        # Bottom bar: always-on-top + settings
        bottom = tk.Frame(container, bg=COLORS["bg"])
        bottom.pack(fill=tk.X, pady=(8, 0))

        self.var_ontop = tk.BooleanVar(value=self.settings.get("always_on_top", False))
        cb_ontop = tk.Checkbutton(
            bottom,
            text="始终置顶",
            variable=self.var_ontop,
            command=self._toggle_ontop,
            bg=COLORS["bg"],
            fg=COLORS["fg"],
            selectcolor=COLORS["bg"],
            activebackground=COLORS["bg"],
            cursor="hand2",
        )
        cb_ontop.pack(side=tk.LEFT)

        btn_settings = tk.Button(
            bottom, text="⚙ 设置", font=("Microsoft YaHei UI", 9),
            command=self._open_settings,
            bg=COLORS["bg"], fg=COLORS["fg"],
            relief=tk.FLAT, cursor="hand2",
            activebackground=COLORS["button_bg"],
        )
        btn_settings.pack(side=tk.RIGHT)

        # Keyboard shortcuts
        self.bind("<space>", lambda e: self._toggle_start_pause())
        self.bind("<r>", lambda e: self.reset_timer())
        self.bind("<s>", lambda e: self.skip_session())
        self.bind("<Control-s>", lambda e: self._open_settings())

    # ── Timer logic ──────────────────────────────────────────────────────

    def start_timer(self):
        """Start or resume the countdown."""
        if self.running and not self.paused:
            return  # already running
        self.running = True
        self.paused = False
        self._start_ts = time.monotonic()
        self._schedule_tick()
        self._update_button_states()

    def _cancel_tick(self):
        """Cancel any pending tick callback."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def pause_timer(self):
        """Pause the countdown."""
        if not self.running or self.paused:
            return
        self.paused = True
        self._cancel_tick()
        self._update_button_states()

    def reset_timer(self):
        """Reset the current session to its initial duration."""
        self.running = False
        self.paused = False
        self._cancel_tick()
        self.remaining_sec = self._get_session_seconds()
        self._update_display()
        self._update_button_states()

    def skip_session(self):
        """Skip to the next session immediately."""
        self._cancel_tick()
        self._complete_session()

    def _toggle_start_pause(self):
        """Spacebar handler — start or pause."""
        if self.running and not self.paused:
            self.pause_timer()
        else:
            self.start_timer()

    def _schedule_tick(self):
        """Schedule the next 1-second tick."""
        if not self.running or self.paused:
            return
        self._after_id = self.after(1000, self._tick)

    def _tick(self):
        """One second has elapsed. Decrement the counter."""
        if not self.running or self.paused:
            return

        # Accurate timing — deduct real elapsed seconds to compensate for drift
        now = time.monotonic()
        elapsed = int(now - self._start_ts)
        self._start_ts = now
        self.remaining_sec = max(0, self.remaining_sec - elapsed)

        self._update_display()

        if self.remaining_sec <= 0:
            self._complete_session()
        else:
            self._schedule_tick()

    def _complete_session(self):
        """Called when the current session reaches 00:00."""
        self.running = False
        self.paused = False
        self._cancel_tick()

        # If this was a work session, increment work count
        if self.session == WORK:
            self.work_count += 1
            self._update_progress_dots()

        self._notify()
        self._next_session()

    def _next_session(self):
        """Advance to the next session in the cycle."""
        if self.session == WORK:
            if self.work_count > 0 and self.work_count % self.settings["long_break_interval"] == 0:
                self.session = LONG_BREAK
                self.work_count = 0  # reset cycle
                self._update_progress_dots()
            else:
                self.session = SHORT_BREAK
        else:
            self.session = WORK
        self.remaining_sec = self._get_session_seconds()

        self._update_display()
        self._update_button_states()
        # Auto-start the next session
        self.start_timer()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _get_session_seconds(self):
        """Return the full duration in seconds for the current session type."""
        return self.settings[SESSION_MINUTE_KEY[self.session]] * 60

    def _update_display(self):
        """Refresh the countdown label and session indicator."""
        mins, secs = divmod(self.remaining_sec, 60)
        self.lbl_timer.config(text=f"{mins:02d}:{secs:02d}")
        self.lbl_session.config(text=SESSION_LABELS[self.session])

        # Update timer background color to match session
        color = COLORS[self.session]
        self.timer_bg.config(bg=color)
        self.lbl_timer.config(bg=color)

    def _build_progress_dots(self):
        """Create or recreate all progress dot labels."""
        for d in self.dot_labels:
            d.destroy()
        self.dot_labels.clear()
        max_dots = self.settings["long_break_interval"]
        for _ in range(max_dots):
            dot = tk.Label(
                self.dots_frame, text="●", font=("", 16),
                bg=COLORS["bg"], fg=COLORS["dot_empty"],
            )
            dot.pack(side=tk.LEFT, padx=3)
            self.dot_labels.append(dot)
        self._update_progress_dots()

    def _update_progress_dots(self):
        """Refresh dot colors to reflect completed work sessions."""
        for i, dot in enumerate(self.dot_labels):
            dot.config(
                fg=COLORS["dot_filled"] if i < self.work_count else COLORS["dot_empty"]
            )

    def _update_button_states(self):
        """Enable/disable buttons based on current state."""
        if self.running and not self.paused:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
        elif self.running and self.paused:
            self.btn_start.config(state=tk.NORMAL, text="▶ 继续")
            self.btn_pause.config(state=tk.DISABLED)
        else:
            self.btn_start.config(state=tk.NORMAL, text="▶ 开始")
            self.btn_pause.config(state=tk.DISABLED)

    def _notify(self):
        """Alert the user that a session has ended."""
        # Sound
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            pass

        # Flash the taskbar / bring window to front
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass

        # Set a temporary flash via title
        orig_title = self.title()
        if self.session == WORK:
            flash_text = "✅ 工作完成！休息一下"
        else:
            flash_text = "⏰ 休息结束！开始工作"
        # Flash once
        self.title(flash_text)
        self.after(3000, lambda: self.title(orig_title))

    def _toggle_ontop(self):
        """Toggle the always-on-top window attribute."""
        on = self.var_ontop.get()
        self.attributes("-topmost", on)
        self.settings["always_on_top"] = on
        save_settings(self.settings)

    def _open_settings(self):
        """Open the settings dialog."""
        was_running = self.running and not self.paused
        if was_running:
            self.pause_timer()

        SettingsDialog(self, self.settings, self._on_settings_saved)

    def _on_settings_saved(self, new_settings):
        """Callback after settings dialog saves."""
        self.settings = new_settings
        self.reset_timer()
        self._build_progress_dots()

    def _center_window(self):
        """Position the window at screen center."""
        _center_window(self)

    def _on_close(self):
        """Handle window close — persist settings."""
        save_settings(self.settings)
        self.destroy()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = PomodoroTimer()
    app.mainloop()


if __name__ == "__main__":
    main()
