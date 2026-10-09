"""protean-edu command contract. No Hermes install required to run these tests."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("protean_edu", ROOT / "__init__.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class FakeCtx:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, handler, description="", args_hint=""):
        self.commands[name] = {
            "handler": handler,
            "description": description,
            "args_hint": args_hint,
        }


def test_register_uses_edu(tmp_path, monkeypatch):
    ctx = FakeCtx()
    mod.register(ctx)
    assert "edu" in ctx.commands
    assert ctx.commands["edu"]["handler"] is mod.handle


def test_on_writes_state(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    # force the fallback path even if hermes_constants imports
    monkeypatch.setattr(mod, "state_path", lambda: tmp_path / "protean-edu-state.json")
    text = mod.handle("on")
    data = json.loads((tmp_path / "protean-edu-state.json").read_text())
    assert data["enabled"] is True
    assert "on" in text


def test_off_keeps_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "state_path", lambda: tmp_path / "protean-edu-state.json")
    mod.save_state({"enabled": True, "level": 2, "lesson": "files"})
    text = mod.handle("off")
    data = json.loads((tmp_path / "protean-edu-state.json").read_text())
    assert data["enabled"] is False
    assert data["level"] == 2
    assert data["lesson"] == "files"
    assert "off" in text


def test_unknown_shows_help(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "state_path", lambda: tmp_path / "protean-edu-state.json")
    text = mod.handle("nope")
    assert "Unknown command: nope" in text
    assert "/edu on" in text


def test_next_requires_on(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "state_path", lambda: tmp_path / "protean-edu-state.json")
    text = mod.handle("next")
    assert "Teaching is off" in text
