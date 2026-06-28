# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Pomodoro desktop timer — single-file Python + tkinter GUI with zero external dependencies.
- Canvas-based circular timer with arc progress ring
- 5 color themes (Tailwind CSS palette)
- Custom countdown mode (user-set duration)
- Settings persist to `~/.pomodoro_settings.json`
- Built for Windows (`pythonw` to suppress console, `winsound` for alerts)

## Run

```bash
python pomodoro.py          # normal launch (with console window)
pythonw pomodoro.py         # no console window
run.bat                     # double-click launcher (uses pythonw)
```

**Keyboard shortcuts:** `Space` start/pause, `R` reset, `S` skip, `Ctrl+S` settings.

## Project files

```
pomodoro.py          # Entire application (~700 lines)
run.bat              # Windows double-click launcher: start "" pythonw pomodoro.py
.gitignore           # Python + __pycache__ + VSCode + .pomodoro_settings.json
CLAUDE.md            # This file
```

Settings stored at `~/.pomodoro_settings.json`:
```json
{"work_minutes": 25, "short_break_minutes": 5, "long_break_minutes": 15,
 "long_break_interval": 4, "always_on_top": false, "theme": "sunset",
 "last_custom_minutes": 30}
```

## Architecture

**`pomodoro.py`** single-file app with these components:

### Session state machine
```
IDLE → RUNNING ↔ PAUSED → RUNNING → ... → COMPLETE → auto-next → ...
  ↑         ↓                                       ↑
  └─ RESET ─┘                                       └─ auto-start (in _next_session)
```
- Cycle: WORK → SHORT_BREAK → WORK → SHORT_BREAK → … → LONG_BREAK → repeat
- **CUSTOM** mode: user sets minutes → timer runs → stops at 00:00 (no auto-advance) → Reset/Skip returns to saved session
- When a session hits 00:00, `_complete_session()` calls `_notify()` then `_next_session()` — sessions **always auto-start** the next one (except CUSTOM)
- Timer accuracy: `time.monotonic()` drift compensation

### Key classes and functions
- **`PomodoroTimer(tk.Tk)`** — main window and state machine
- **`SettingsDialog(tk.Toplevel)`** — modal settings popup; validates input, saves + callback
- **`load_settings()` / `save_settings()`** — JSON I/O with `pathlib.Path.home()`; merged with defaults
- **`_center_window(win, parent=None)`** — module-level geometry helper

### Timer display (Canvas)
```
create_oval (filled circle)            → self._timer_circle
create_arc (track ring, dot_empty)     → self._track_ring
create_arc (progress ring, white)      → self._progress_ring
create_text (MM:SS, Consolas 40px)     → self._timer_text
create_text (session label, 11px)      → self._session_canvas_text
```
- Arc progress: `start=90` (12 o'clock), `extent=-360 * elapsed` (clockwise fill)
- Canvas 260×260, circle center at (130, 125), radius 100

### Theme system
- `THEMES` dict: 5 themes (sunset/ocean/midnight/forest/lavender), each with 12 color keys
- `COLORS` module-level dict mutated on switch: `COLORS.clear(); COLORS.update(THEMES[name])`
- Session type colors (WORK/SHORT_BREAK/LONG_BREAK) + bg/fg/button_bg/dot_empty/dot_filled
- Button colors as `(bg, activebackground)` tuples: btn_start/pause/reset/skip
- Theme switching: Settings dialog → `_on_settings_saved()` → `_apply_theme()`
- CUSTOM session falls back to WORK color: `COLORS.get(CUSTOM, COLORS[WORK])`

### Progress bar (Canvas)
- Segments per `long_break_interval`, filled = `dot_filled` / empty = `dot_empty`
- Destroyed and rebuilt when interval changes (`_build_progress_bar()`)
- Hidden during CUSTOM mode (`pack_forget()` / `pack()`)

### Design patterns
- `SESSION_MINUTE_KEY` dict maps session type → settings key, avoids if/elif chains
- `_cancel_tick()` helper to avoid repeating `after_cancel` + `None` assignment
- Inner function `_btn()` factory inside `_build_ui()` reduces button boilerplate
- `_build_progress_bar` / `_update_progress_bar` split: rebuild only on interval change, recolor on every completed work session

## Git

```bash
git push origin main          # push changes
```

Proxy configured globally (`git config --global http.proxy http://127.0.0.1:7890`) — needed to reach GitHub from this network. If push fails with connection errors, verify the proxy is running on port 7890.

GitHub remote: `https://github.com/zoucc-git/First.cc.git` (origin/main).
