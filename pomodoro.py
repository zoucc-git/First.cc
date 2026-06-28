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
    "theme": "sunset",
    "last_custom_minutes": 30,
}

# ── Session types ────────────────────────────────────────────────────────────

WORK = "work"
SHORT_BREAK = "short_break"
LONG_BREAK = "long_break"
CUSTOM = "custom"

SESSION_LABELS = {
    WORK: "\U0001f345 工作中",
    SHORT_BREAK: "☕ 短休息",
    LONG_BREAK: "\U0001f330 长休息",
    CUSTOM: "⏱ 自定义",
}

SESSION_MINUTE_KEY = {
    WORK: "work_minutes",
    SHORT_BREAK: "short_break_minutes",
    LONG_BREAK: "long_break_minutes",
}

# ── Color themes ──────────────────────────────────────────────────────────────

THEMES = {
    "sunset": {
        WORK: "#e85d4a",        # coral
        SHORT_BREAK: "#f59e0b", # amber-500
        LONG_BREAK: "#a855f7",  # purple-500
        "bg": "#fff7ed",        # orange-50
        "fg": "#431407",        # orange-950
        "button_bg": "#ffedd5", # orange-100
        "dot_empty": "#fed7aa", # orange-200
        "dot_filled": "#f97316",# orange-500
        # all buttons in orange/amber family
        "btn_start": ("#c2410c", "#ea580c"),
        "btn_pause": ("#d97706", "#f59e0b"),
        "btn_reset": ("#a16207", "#ca8a04"),
        "btn_skip": ("#854d0e", "#a16207"),
    },
    "ocean": {
        WORK: "#ef4444",        # red-500
        SHORT_BREAK: "#06b6d4", # cyan-500
        LONG_BREAK: "#6366f1",  # indigo-500
        "bg": "#f0f9ff",        # sky-50
        "fg": "#082f49",        # sky-950
        "button_bg": "#e0f2fe", # sky-100
        "dot_empty": "#bae6fd", # sky-200
        "dot_filled": "#0ea5e9",# sky-500
        # all buttons in cool blue/cyan family
        "btn_start": ("#0284c7", "#38bdf8"),
        "btn_pause": ("#0891b2", "#06b6d4"),
        "btn_reset": ("#6366f1", "#818cf8"),
        "btn_skip": ("#475569", "#64748b"),
    },
    "midnight": {
        WORK: "#f87171",        # red-400
        SHORT_BREAK: "#34d399", # emerald-400
        LONG_BREAK: "#818cf8",  # indigo-400
        "bg": "#0f172a",        # slate-900
        "fg": "#f1f5f9",        # slate-100
        "button_bg": "#1e293b", # slate-800
        "dot_empty": "#334155", # slate-700
        "dot_filled": "#fbbf24",# amber-400
        # bright accent buttons on dark background
        "btn_start": ("#dc2626", "#ef4444"),
        "btn_pause": ("#059669", "#34d399"),
        "btn_reset": ("#f59e0b", "#fbbf24"),
        "btn_skip": ("#4b5563", "#6b7280"),
    },
    "forest": {
        WORK: "#e85d4a",        # coral
        SHORT_BREAK: "#10b981", # emerald-500
        LONG_BREAK: "#3b82f6",  # blue-500
        "bg": "#ecfdf5",        # emerald-50
        "fg": "#022c22",        # emerald-950
        "button_bg": "#d1fae5", # emerald-100
        "dot_empty": "#a7f3d0", # emerald-200
        "dot_filled": "#059669",# emerald-600
        # green family + red start as accent
        "btn_start": ("#dc2626", "#ef4444"),
        "btn_pause": ("#059669", "#10b981"),
        "btn_reset": ("#0d9488", "#14b8a6"),
        "btn_skip": ("#4b5563", "#6b7280"),
    },
    "lavender": {
        WORK: "#e85d4a",        # coral
        SHORT_BREAK: "#d946ef", # fuchsia-500
        LONG_BREAK: "#6366f1",  # indigo-500
        "bg": "#f5f3ff",        # violet-50
        "fg": "#2e1065",        # violet-950
        "button_bg": "#ede9fe", # violet-100
        "dot_empty": "#ddd6fe", # violet-200
        "dot_filled": "#8b5cf6",# violet-500
        # purple/pink/fuchsia family
        "btn_start": ("#9333ea", "#a855f7"),
        "btn_pause": ("#db2777", "#ec4899"),
        "btn_reset": ("#c026d3", "#d946ef"),
        "btn_skip": ("#6b7280", "#9ca3af"),
    },
}

THEME_NAMES = {
    "sunset": "🌅 暖阳",
    "ocean": "🌊 海洋",
    "midnight": "🌙 午夜",
    "forest": "🌲 森林",
    "lavender": "🌸 薰衣草",
}

THEME_DISPLAY_TO_KEY = {v: k for k, v in THEME_NAMES.items()}

# Active theme (module-level dict, mutated on theme switch — existing code
# references COLORS[...] and picks up the change automatically).
COLORS = dict(THEMES["sunset"])


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

        # Theme selector
        self.theme_var = tk.StringVar(
            value=THEME_NAMES.get(self.settings.get("theme", "sunset"), "🌅 夕阳")
        )
        ttk.Label(frame, text="配色方案:", width=18).pack(pady=(12, 3))
        self.theme_combo = ttk.Combobox(
            frame, textvariable=self.theme_var,
            values=list(THEME_NAMES.values()),
            state="readonly", width=16,
        )
        self.theme_combo.pack()

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
            # Save theme
            display = self.theme_var.get()
            self.settings["theme"] = THEME_DISPLAY_TO_KEY.get(display, "sunset")
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

        # Set active theme from saved settings
        theme_name = self.settings.get("theme", "sunset")
        if theme_name not in THEMES:
            theme_name = "sunset"
        COLORS.clear()
        COLORS.update(THEMES[theme_name])

        self.session = WORK              # current session type
        self.remaining_sec = self.settings["work_minutes"] * 60
        self.running = False
        self.paused = False
        self.work_count = 0              # completed work sessions in current cycle
        self._after_id = None            # tkinter after callback id
        self._start_ts = None            # wall-clock time when current tick started
        self._saved_session = WORK       # session before entering custom mode

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
        # Main self.container
        self.container = tk.Frame(self, bg=COLORS["bg"], padx=30, pady=20)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Timer display (Canvas circular)
        self._build_timer_canvas()

        # Progress bar (work session progress)
        self._build_progress_bar()

        # Control buttons
        btn_frame = tk.Frame(self.container, bg=COLORS["bg"])
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

        self.btn_start = _btn("▶ 开始", self.start_timer, *COLORS["btn_start"])
        self.btn_pause = _btn("⏸ 暂停", self.pause_timer, *COLORS["btn_pause"])
        self.btn_reset = _btn("↺ 重置", self.reset_timer, *COLORS["btn_reset"])
        self.btn_skip = _btn("⏭ 跳过", self.skip_session, *COLORS["btn_skip"])

        # Custom timer row
        self.custom_frame = tk.Frame(self.container, bg=COLORS["bg"])
        self.custom_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            self.custom_frame, text="⏱", font=("", 10),
            bg=COLORS["bg"], fg=COLORS["fg"],
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.spin_custom = ttk.Spinbox(
            self.custom_frame, from_=1, to=999, width=5, justify=tk.CENTER,
        )
        self.spin_custom.set(str(self.settings.get("last_custom_minutes", 30)))
        self.spin_custom.pack(side=tk.LEFT)
        tk.Label(
            self.custom_frame, text="分", font=("", 10),
            bg=COLORS["bg"], fg=COLORS["fg"],
        ).pack(side=tk.LEFT, padx=(4, 8))
        self.btn_custom = tk.Button(
            self.custom_frame, text="⏱ 自定义计时",
            font=("Microsoft YaHei UI", 9),
            command=self._start_custom_timer,
            bg=COLORS["button_bg"], fg=COLORS["fg"],
            relief=tk.FLAT, cursor="hand2",
            activebackground=COLORS["dot_filled"],
        )
        self.btn_custom.pack(side=tk.LEFT)

        # ---- Bottom bar: always-on-top + settings ----
        bottom = tk.Frame(self.container, bg=COLORS["bg"])
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

    def _build_timer_canvas(self):
        """Create circular timer display with progress ring."""
        cvs_size = 260
        cx = cvs_size // 2
        cy = 125
        r = 100

        self.timer_canvas = tk.Canvas(
            self.container,
            width=cvs_size, height=cvs_size,
            bg=COLORS["bg"], highlightthickness=0,
        )
        self.timer_canvas.pack(pady=(0, 10))

        # Outer bezel ring (subtle border for depth)
        self._bezel_ring = self.timer_canvas.create_oval(
            cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2,
            outline=COLORS["dot_empty"], width=1,
        )

        # Filled circle background
        self._timer_circle = self.timer_canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COLORS[WORK], outline="",
        )

        # Track ring (background of progress ring)
        self._track_ring = self.timer_canvas.create_arc(
            cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7,
            start=90, extent=-360,
            outline=COLORS["dot_empty"],
            width=3, style="arc",
        )

        # Progress ring (fills as time elapses)
        self._progress_ring = self.timer_canvas.create_arc(
            cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7,
            start=90, extent=0,
            outline="white",
            width=3, style="arc",
        )

        # Timer text (large MM:SS)
        self._timer_text = self.timer_canvas.create_text(
            cx, cy - 4,
            text="25:00",
            font=("Consolas", 40, "bold"),
            fill="white", anchor="center",
        )

        # Session label inside circle
        self._session_canvas_text = self.timer_canvas.create_text(
            cx, cy + 36,
            text="", font=("Microsoft YaHei UI", 11),
            fill="white", anchor="center",
        )

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
        # If coming back from custom mode, restore saved session
        if self.session == CUSTOM:
            self.session = self._saved_session
            self.btn_custom.config(state=tk.NORMAL)
            self.progress_canvas.pack(pady=(0, 16))
        self.remaining_sec = self._get_session_seconds()
        self._update_display()
        self._update_button_states()

    def skip_session(self):
        """Skip to the next session immediately."""
        self._cancel_tick()
        # In custom mode, skip goes back to saved session
        if self.session == CUSTOM:
            self.reset_timer()
        else:
            self._complete_session()

    def _toggle_start_pause(self):
        """Spacebar handler — start or pause."""
        if self.running and not self.paused:
            self.pause_timer()
        else:
            self.start_timer()

    def _start_custom_timer(self):
        """Start a custom countdown with user-specified minutes."""
        # Read spinbox value
        try:
            minutes = int(self.spin_custom.get())
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数字。")
            return
        if minutes < 1:
            messagebox.showwarning("输入错误", "分钟数不能小于 1。")
            return

        # Save current session for later restore
        self._saved_session = self.session
        # Persist the value
        self.settings["last_custom_minutes"] = minutes
        save_settings(self.settings)

        # Cancel any running timer
        self._cancel_tick()

        # Switch to custom mode
        self.session = CUSTOM
        self._custom_total_sec = minutes * 60
        self.remaining_sec = self._custom_total_sec
        self.running = False
        self.paused = False
        self.btn_custom.config(state=tk.DISABLED)

        # Hide progress bar during custom timer
        self.progress_canvas.pack_forget()

        self._update_display()
        self._update_button_states()
        # Auto-start
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
        # Custom mode: notify, stay at 00:00, don't auto-advance
        if self.session == CUSTOM:
            self.running = False
            self.paused = False
            self._cancel_tick()
            self._notify()
            self.btn_custom.config(state=tk.NORMAL)
            self.progress_canvas.pack(pady=(0, 16))
            self._update_button_states()
            return

        self.running = False
        self.paused = False
        self._cancel_tick()

        # If this was a work session, increment work count
        if self.session == WORK:
            self.work_count += 1
            self._update_progress_bar()

        self._notify()
        self._next_session()

    def _next_session(self):
        """Advance to the next session in the cycle."""
        if self.session == WORK:
            if self.work_count > 0 and self.work_count % self.settings["long_break_interval"] == 0:
                self.session = LONG_BREAK
                self.work_count = 0  # reset cycle
                self._update_progress_bar()
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
        """Refresh countdown, progress ring, and session indicator."""
        mins, secs = divmod(self.remaining_sec, 60)
        self.timer_canvas.itemconfig(self._timer_text, text=f"{mins:02d}:{secs:02d}")
        self.timer_canvas.itemconfig(
            self._session_canvas_text, text=SESSION_LABELS[self.session]
        )

        # Update progress ring (fills as time elapses)
        if self.session == CUSTOM:
            # Use saved custom total for progress calculation
            total = getattr(self, "_custom_total_sec", self.remaining_sec)
        else:
            total = self._get_session_seconds()
        elapsed = 1 - (self.remaining_sec / total) if total > 0 else 1
        self.timer_canvas.itemconfig(self._progress_ring, extent=-360 * elapsed)

        # Circle color — CUSTOM falls back to WORK color
        color = COLORS.get(self.session, COLORS[WORK])
        self.timer_canvas.itemconfig(self._timer_circle, fill=color)

    def _build_progress_bar(self):
        """Create progress bar showing completed work sessions."""
        # Destroy old canvas to avoid stacking on theme switch
        if hasattr(self, "progress_canvas"):
            self.progress_canvas.destroy()
        max_seg = self.settings["long_break_interval"]
        bar_w = 200
        gap = 4
        seg_w = (bar_w - (max_seg - 1) * gap) / max_seg
        h = 10

        self.progress_canvas = tk.Canvas(
            self.container,
            width=bar_w, height=h + 12,
            bg=COLORS["bg"], highlightthickness=0,
        )
        self.progress_canvas.pack(pady=(0, 16))

        # Background track
        self.progress_canvas.create_rectangle(
            0, 6, bar_w, h + 6,
            fill=COLORS["dot_empty"],
            outline="", width=0,
        )

        self._progress_segments = []
        for i in range(max_seg):
            x1 = i * (seg_w + gap)
            x2 = x1 + seg_w
            seg = self.progress_canvas.create_rectangle(
                x1, 6, x2, h + 6,
                fill=COLORS["dot_empty"],
                outline=COLORS["bg"], width=1,
            )
            self._progress_segments.append(seg)
        self._update_progress_bar()

    def _update_progress_bar(self):
        """Refresh segment colors to match completed work count."""
        for i, seg in enumerate(self._progress_segments):
            self.progress_canvas.itemconfig(
                seg,
                fill=COLORS["dot_filled"] if i < self.work_count else COLORS["dot_empty"],
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

    def _apply_theme(self):
        """Update all existing widgets to match the active theme colors."""
        c = COLORS
        self.configure(bg=c["bg"])
        self.container.configure(bg=c["bg"])
        # Canvas timer
        self.timer_canvas.configure(bg=c["bg"])
        self.timer_canvas.itemconfig(self._timer_circle, fill=c.get(self.session, c[WORK]))
        self.timer_canvas.itemconfig(self._track_ring, outline=c["dot_empty"])
        self.timer_canvas.itemconfig(self._bezel_ring, outline=c["dot_empty"])
        # Canvas progress bar
        self.progress_canvas.configure(bg=c["bg"])
        self._update_progress_bar()
        # Buttons
        bg, abg = c["btn_start"]
        self.btn_start.configure(bg=bg, activebackground=abg)
        bg, abg = c["btn_pause"]
        self.btn_pause.configure(bg=bg, activebackground=abg)
        bg, abg = c["btn_reset"]
        self.btn_reset.configure(bg=bg, activebackground=abg)
        bg, abg = c["btn_skip"]
        self.btn_skip.configure(bg=bg, activebackground=abg)
        # Bottom bar
        self.cb_ontop.configure(
            bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], activebackground=c["bg"]
        )
        self.btn_settings.configure(
            bg=c["bg"], fg=c["fg"], activebackground=c["button_bg"]
        )
        # Custom frame (guard in case theme is applied before _build_ui)
        if hasattr(self, "custom_frame"):
            for child in self.custom_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=c["bg"], fg=c["fg"])
                elif isinstance(child, tk.Button):
                    child.configure(bg=c["button_bg"], fg=c["fg"],
                                    activebackground=c["dot_filled"])

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
        # Apply theme if changed
        theme = self.settings.get("theme", "sunset")
        COLORS.clear()
        COLORS.update(THEMES.get(theme, THEMES["sunset"]))
        self._apply_theme()
        self.reset_timer()
        self._build_progress_bar()

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
