"""protean-edu command contract. No Hermes install required to run these tests."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("protean_edu", ROOT / "__init__.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "lessons"


class FakeCtx:
    def __init__(self):
        self.commands = {}
        self.hooks = {}

    def register_command(self, name, handler, description="", args_hint=""):
        self.commands[name] = {
            "handler": handler,
            "description": description,
            "args_hint": args_hint,
        }

    def register_hook(self, hook_name, callback):
        self.hooks[hook_name] = callback


def _use_fixtures(monkeypatch, tmp_path):
    """Point the module at the fixture lessons dir and a scratch state file."""
    monkeypatch.setattr(mod, "lessons_dir", lambda: FIXTURES)
    monkeypatch.setattr(mod, "state_path", lambda: tmp_path / "protean-edu-state.json")


def _state(tmp_path):
    p = tmp_path / "protean-edu-state.json"
    return json.loads(p.read_text()) if p.is_file() else None


def test_register_uses_edu_and_hook(tmp_path, monkeypatch):
    ctx = FakeCtx()
    mod.register(ctx)
    assert "edu" in ctx.commands
    assert ctx.commands["edu"]["handler"] is mod.handle
    assert ctx.hooks["pre_llm_call"] is mod.pre_llm_call


def test_on_writes_state(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    text = mod.handle("on")
    data = _state(tmp_path)
    assert data["enabled"] is True
    assert "on" in text


def test_on_preserves_level_and_lesson(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": False, "level": 2, "lesson": "prompts"})
    mod.handle("on")
    data = _state(tmp_path)
    assert data["enabled"] is True
    assert data["level"] == 2
    assert data["lesson"] == "prompts"


def test_off_keeps_progress(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 2, "lesson": "prompts"})
    text = mod.handle("off")
    data = _state(tmp_path)
    assert data["enabled"] is False
    assert data["level"] == 2
    assert data["lesson"] == "prompts"
    assert "off" in text


def test_off_never_deletes_state_file(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    mod.handle("off")
    assert _state(tmp_path) is not None


def test_status_reads_only(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    text = mod.handle("status")
    assert "on" in text
    # status must not write anything
    assert _state(tmp_path)["enabled"] is True


def test_unknown_shows_help(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    text = mod.handle("nope")
    assert "Unknown command: nope" in text
    assert "/edu on" in text


def test_next_requires_on(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    text = mod.handle("next")
    assert "Teaching is off" in text


def test_next_yes_requires_on(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    text = mod.handle("next yes")
    assert "Teaching is off" in text


def test_next_bare_prints_lesson_and_proof_run_writes_nothing(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    text = mod.handle("next")
    assert "Lesson 1: Reading a diff" in text
    assert "Open the file the agent says it changed and read the diff." in text
    assert "When the check passes, run: /edu next yes" in text
    # bare next writes nothing
    assert _state(tmp_path)["level"] == 1


def test_next_yes_advances(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    text = mod.handle("next yes")
    data = _state(tmp_path)
    assert data["level"] == 2
    assert data["lesson"] == "prompts"
    assert "Lesson 2: prompts" in text


def test_next_yes_at_last_lesson_stays(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 4, "lesson": "tests"})
    text = mod.handle("next yes")
    data = _state(tmp_path)
    # no lesson 5 file exists -> student stays, no gap skipped
    assert data["level"] == 4
    assert data["lesson"] == "tests"
    assert "There is no lesson 5 yet" in text


def test_next_refuses_on_missing_lesson(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 9, "lesson": "nonexistent"})
    text = mod.handle("next")
    assert "There is no lesson 9 yet." in text
    assert _state(tmp_path)["level"] == 9


def test_next_yes_refuses_on_missing_lesson(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 9, "lesson": "nonexistent"})
    text = mod.handle("next yes")
    assert "There is no lesson 9 yet." in text
    assert _state(tmp_path)["level"] == 9


def test_next_refuses_on_malformed_lesson(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 3, "lesson": "broken"})
    text = mod.handle("next")
    assert "Lesson 3 is malformed" in text
    assert _state(tmp_path)["level"] == 3


def test_next_yes_refuses_on_malformed_lesson(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 3, "lesson": "broken"})
    text = mod.handle("next yes")
    assert "Lesson 3 is malformed" in text
    assert _state(tmp_path)["level"] == 3


def test_review_is_read_only(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    text = mod.handle("review")
    assert "Lesson 1: Reading a diff" in text
    assert "A diff shows exactly what changed." in text
    assert "Open the file the agent says it changed and read the diff." in text
    # review writes nothing
    assert _state(tmp_path)["level"] == 1


def test_review_requires_on(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    text = mod.handle("review")
    assert "Teaching is off" in text


def test_help_lists_commands(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    text = mod.handle("help")
    for cmd in ("on", "off", "status", "next", "review", "help"):
        assert f"/edu {cmd}" in text


def test_injection_under_160(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    out = mod.pre_llm_call()
    assert out is not None
    assert len(out) <= 160
    assert out.startswith("[protean-edu] 1: Reading a diff. Check: ")


def test_injection_noop_when_off(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": False, "level": 1, "lesson": "reading-a-diff"})
    assert mod.pre_llm_call() is None


def test_injection_noop_when_lesson_null(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 1, "lesson": None})
    assert mod.pre_llm_call() is None


def test_injection_noop_when_lesson_missing(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 9, "lesson": "nonexistent"})
    assert mod.pre_llm_call() is None


def test_injection_noop_when_lesson_malformed(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    mod.save_state({"enabled": True, "level": 3, "lesson": "broken"})
    assert mod.pre_llm_call() is None


def test_injection_cap_with_overlong_title(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    # A lesson whose title and check line would far exceed 160 chars.
    long_title = "How to read a very long and detailed diff that keeps going and going and going"
    long_check = (
        "Open the file the agent says it changed and read the diff very carefully "
        "and then compare every single line against what the agent claimed to have done"
    )
    monkeypatch.setattr(
        mod, "parse_lesson",
        lambda level: {
            "ok": True, "reason": None, "title": long_title,
            "why": "x", "check": long_check, "next": "x",
        },
    )
    mod.save_state({"enabled": True, "level": 1, "lesson": "reading-a-diff"})
    out = mod.pre_llm_call()
    assert out is not None
    assert len(out) <= 160
    assert out.startswith("[protean-edu]")


def test_state_setdefault_keeps_partial_file_valid(tmp_path, monkeypatch):
    _use_fixtures(monkeypatch, tmp_path)
    # A partial file with only one key must stay valid after load_state.
    (tmp_path / "protean-edu-state.json").write_text(json.dumps({"enabled": True}))
    data = mod.load_state()
    assert data["enabled"] is True
    assert data["level"] == 1
    assert data["lesson"] is None
