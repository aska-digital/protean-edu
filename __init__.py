"""protean-edu — educational mode for Hermes.

A plugin, not a fork. /edu is registered through the plugin command API.
State lives in a file under HERMES_HOME so a restart can read it.
"""

from __future__ import annotations

import json
from pathlib import Path

STATE_NAME = "protean-edu-state.json"


def state_path() -> Path:
    """Profile-safe. Never hardcode ~/.hermes."""
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:
        import os
        home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    return home / STATE_NAME


def load_state() -> dict:
    path = state_path()
    if not path.is_file():
        return {"enabled": False, "level": 1, "lesson": None}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"enabled": False, "level": 1, "lesson": None}
    if not isinstance(data, dict):
        return {"enabled": False, "level": 1, "lesson": None}
    data.setdefault("enabled", False)
    data.setdefault("level", 1)
    data.setdefault("lesson", None)
    return data


def save_state(data: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


HELP = """protean-edu — learn to read the code your agents write.

/edu on       Turn teaching on for this profile.
/edu off      Turn teaching off. Your agents keep working. The lessons stop.
/edu status   Show whether teaching is on, and which lesson you are on.
/edu next     Mark the current lesson done and show the next one.
/edu help     Show this list.

Teaching is off until you turn it on. Turning it off does not delete progress.
"""


def _status_line(data: dict) -> str:
    state = "on" if data.get("enabled") else "off"
    lesson = data.get("lesson") or "none yet"
    return f"protean-edu is {state}. Level {data.get('level', 1)}. Lesson: {lesson}."


def handle(raw_args: str) -> str:
    argv = (raw_args or "").strip().split()
    cmd = argv[0].lower() if argv else "help"
    data = load_state()

    if cmd in {"help", "-h", "--help"}:
        return HELP
    if cmd == "on":
        data["enabled"] = True
        save_state(data)
        return _status_line(data) + "\n\nI will explain the decision, the command, and what you can check yourself. I still do the work."
    if cmd == "off":
        data["enabled"] = False
        save_state(data)
        return _status_line(data)
    if cmd == "status":
        return _status_line(data)
    if cmd == "next":
        if not data.get("enabled"):
            return "Teaching is off. Run /edu on first.\n\n" + _status_line(data)
        return "No lesson is loaded yet. The first lesson lands after the curriculum is written.\n\n" + _status_line(data)
    return f"Unknown command: {cmd}\n\n{HELP}"


def register(ctx) -> None:
    ctx.register_command(
        "edu",
        handler=handle,
        description="Turn educational mode on or off, and step through lessons.",
        args_hint="on|off|status|next|help",
    )
