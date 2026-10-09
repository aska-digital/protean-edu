"""protean-edu — educational mode for Hermes.

A plugin, not a fork. /edu is registered through the plugin command API.
State lives in a file under HERMES_HOME so a restart can read it.

The contract (docs/contract.md) is the single source of truth for this build.
It binds only to the public plugin surfaces: ctx.register_command, the
pre_llm_call hook, and hermes_constants.get_hermes_home. Everything else is
Python stdlib (json, pathlib, os). No LLM, no shell, no network, no secrets.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

STATE_NAME = "protean-edu-state.json"

# Fixed prefix for the teaching injection (§6).
INJECTION_PREFIX = "[protean-edu]"
# Hard cap on the injection, including the fixed prefix (§6).
INJECTION_CAP = 160
# Title truncation limit before the check line is fitted (§6).
TITLE_CAP = 40

# Required lesson headings, in order (§5).
REQUIRED_HEADINGS = (
    "Why this matters",
    "The idea",
    "Check it yourself",
    "Next",
)


def state_path() -> Path:
    """Profile-safe. Never hardcode ~/.hermes."""
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:
        home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    return home / STATE_NAME


def load_state() -> dict:
    """Read the three-key state file. setdefault keeps a partial file valid (§4)."""
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
    """Write the state file. The only file this plugin ever writes (§6, I6)."""
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def lessons_dir() -> Path:
    """The lessons/ directory at the repo root (§5)."""
    return Path(__file__).resolve().parent / "lessons"


def _truncate(text: str, cap: int) -> str:
    """Truncate to cap characters on a word boundary, appending an ellipsis.

    If the text already fits, return it unchanged. Otherwise cut at the last
    space at or before cap, and append the ellipsis. If there is no space
    boundary (a single unbroken word), hard-cut at cap and append the ellipsis.
    """
    if len(text) <= cap:
        return text
    cut = text[:cap]
    space = cut.rfind(" ")
    if space > 0:
        return cut[:space] + "\u2026"
    return cut + "\u2026"


def parse_lesson(level: int) -> dict:
    """Parse the lesson file for *level* (§5). Deterministic, no LLM.

    Returns a dict with keys: ok (bool), reason (str|None), and on success
    title, why, check, next (str). On failure only ok and reason are set.
    """
    ldir = lessons_dir()
    if not ldir.is_dir():
        return {"ok": False, "reason": f"There is no lesson {level} yet."}

    prefix = f"{level:03d}-"
    try:
        files = sorted(p.name for p in ldir.iterdir() if p.is_file())
    except OSError:
        return {"ok": False, "reason": f"There is no lesson {level} yet."}
    match = [name for name in files if name.startswith(prefix)]
    if not match:
        return {"ok": False, "reason": f"There is no lesson {level} yet."}
    path = ldir / match[0]

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"ok": False, "reason": f"Lesson {level} is malformed (unreadable file)."}

    lines = text.splitlines()

    # H1: "# Lesson N: Title" — N must equal the filename number.
    h1 = next((ln for ln in lines if ln.startswith("# ")), None)
    if h1 is None:
        return {"ok": False, "reason": f"Lesson {level} is malformed (missing title)."}
    h1 = h1[2:].strip()
    if not h1.startswith(f"Lesson {level}:"):
        return {"ok": False, "reason": f"Lesson {level} is malformed (title number mismatch)."}
    title = h1[len(f"Lesson {level}:"):].strip()
    if not title:
        return {"ok": False, "reason": f"Lesson {level} is malformed (empty title)."}

    # Split on lines beginning with "## ". Take the first non-empty line under
    # each required heading.
    sections: dict[str, str] = {}
    current = None
    for ln in lines:
        if ln.startswith("## "):
            current = ln[3:].strip()
            continue
        if current is not None and current in REQUIRED_HEADINGS and current not in sections:
            if ln.strip():
                sections[current] = ln.strip()

    for heading in REQUIRED_HEADINGS:
        if heading not in sections:
            return {"ok": False, "reason": f"Lesson {level} is malformed (missing {heading!r})."}

    return {
        "ok": True,
        "reason": None,
        "title": title,
        "why": sections["Why this matters"],
        "check": sections["Check it yourself"],
        "next": sections["Next"],
    }


def _status_line(data: dict) -> str:
    state = "on" if data.get("enabled") else "off"
    lesson = data.get("lesson") or "none yet"
    return f"protean-edu is {state}. Level {data.get('level', 1)}. Lesson: {lesson}."


def _next_lesson_slug(level: int) -> str | None:
    """The slug of the lesson after *level*, or None if the curriculum is finished.

    Found by sorting lessons/ by filename and matching the LLL- prefix (§5).
    """
    ldir = lessons_dir()
    if not ldir.is_dir():
        return None
    try:
        names = sorted(p.name for p in ldir.iterdir() if p.is_file())
    except OSError:
        return None
    target = f"{level + 1:03d}-"
    for name in names:
        if name.startswith(target):
            stem = name[:-3] if name.endswith(".md") else name
            return stem[len(target):]
    return None


def _lesson_title(level: int) -> str | None:
    """The title of the lesson at *level*, or None if missing/malformed."""
    parsed = parse_lesson(level)
    if not parsed["ok"]:
        return None
    return parsed["title"]


def _handle_next(data: dict, argv: list) -> str:
    """Two-phase /edu next (§7)."""
    if not data.get("enabled"):
        return "Teaching is off. Run /edu on first.\n\n" + _status_line(data)

    level = data.get("level", 1)
    parsed = parse_lesson(level)
    if not parsed["ok"]:
        return parsed["reason"] + "\n\n" + _status_line(data)

    # Bare "/edu next": print the current lesson and its Proof Run. Writes nothing.
    if not argv or argv[0].lower() != "yes":
        return (
            f"Lesson {level}: {parsed['title']}\n"
            f"Proof Run — {parsed['check']}\n"
            "When the check passes, run: /edu next yes"
        )

    # "/edu next yes": record the attestation and advance.
    next_slug = _next_lesson_slug(level)
    if next_slug is None:
        # The next lesson file does not exist. The student stays; no gap is skipped.
        return (
            f"There is no lesson {level + 1} yet. You stay on lesson {level}.\n\n"
            + _status_line(data)
        )

    data["level"] = level + 1
    data["lesson"] = next_slug
    save_state(data)
    next_title = _lesson_title(level + 1)
    title_line = f"Lesson {level + 1}: {next_title}" if next_title else f"Lesson {level + 1}"
    return _status_line(data) + "\n\n" + title_line


def _handle_review(data: dict) -> str:
    """Read-only /edu review (§3, §7). Never judges, never runs the check."""
    if not data.get("enabled"):
        return "Teaching is off. Run /edu on first.\n\n" + _status_line(data)
    level = data.get("level", 1)
    parsed = parse_lesson(level)
    if not parsed["ok"]:
        return parsed["reason"] + "\n\n" + _status_line(data)
    return (
        f"Lesson {level}: {parsed['title']}\n"
        f"Why this matters — {parsed['why']}\n"
        f"Check it yourself — {parsed['check']}"
    )


HELP = """protean-edu — learn to read the code your agents write.

/edu on       Turn teaching on for this profile.
/edu off      Turn teaching off. Your agents keep working. The lessons stop.
/edu status   Show whether teaching is on, and which lesson you are on.
/edu next     Show the current lesson and its Proof Run, then advance with /edu next yes.
/edu review   Show the current lesson's title, why it matters, and its Proof Run. Read-only.
/edu help     Show this list.

Teaching is off until you turn it on. Turning it off does not delete progress.
"""


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
        return _handle_next(data, argv[1:])
    if cmd == "review":
        return _handle_review(data)
    return f"Unknown command: {cmd}\n\n{HELP}"


def _inject() -> str | None:
    """Assemble the teaching injection (§6). Pure function of state + lesson file.

    Returns the injection string, or None for a no-op. Never contains the lesson
    body, the why, glossary, another lesson, LLM output, or personal data.
    """
    data = load_state()
    if not data.get("enabled"):
        return None
    lesson = data.get("lesson")
    if lesson is None:
        return None
    level = data.get("level", 1)
    parsed = parse_lesson(level)
    if not parsed["ok"]:
        return None

    # Fixed prefix + lesson number and title (title truncated at 40 chars).
    title = _truncate(parsed["title"], TITLE_CAP)
    head = f"{INJECTION_PREFIX} {level}: {title}. Check: "
    # Fit the check line to the cap.
    remaining = INJECTION_CAP - len(head)
    if remaining < 1:
        return head[:INJECTION_CAP]
    check = _truncate(parsed["check"], remaining)
    return head + check


def pre_llm_call(**kwargs) -> str | None:
    """The pre_llm_call hook. Appends the injection to the user message only."""
    return _inject()


def register(ctx) -> None:
    ctx.register_command(
        "edu",
        handler=handle,
        description="Turn educational mode on or off, and step through lessons.",
        args_hint="on|off|status|next|review|help",
    )
    ctx.register_hook("pre_llm_call", pre_llm_call)
