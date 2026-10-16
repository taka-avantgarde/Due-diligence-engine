"""Tests for the `dde doctor` environment self-diagnostic command."""

from __future__ import annotations

import pathlib

from click.testing import CliRunner

from due_diligence_engine.cli import _detect_ai_terminal, doctor


def test_doctor_runs_without_crashing():
    """In a normal dev/CI env (reportlab present, Python >= 3.11) doctor prints
    its table and exits cleanly."""
    result = CliRunner().invoke(doctor, [])
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert result.exit_code == 0
    assert "DDE Environment Doctor" in result.output


def test_doctor_survives_unresolvable_home(monkeypatch):
    """Regression: Path.home() raises RuntimeError (NOT OSError) when HOME is
    unset and the UID has no passwd entry (minimal Docker/CI). doctor must
    degrade the ~/Downloads check to a WARN row, never crash."""
    def _boom():
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(pathlib.Path, "home", staticmethod(_boom))
    result = CliRunner().invoke(doctor, [])
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "not resolvable/writable" in result.output  # WARN row, not a traceback


def test_detect_ai_terminal_supports_claude_codex_gemini_antigravity(monkeypatch):
    for env in (
        "CLAUDE_CODE",
        "CODEX_SANDBOX",
        "CODEX_CI",
        "GEMINI_CLI",
        "ANTIGRAVITY_CLI_ALIAS",
        "ANTIGRAVITY_AGENT",
        "CURSOR_SESSION",
        "TERM_PROGRAM",
        "VSCODE_GIT_ASKPASS_NODE",
    ):
        monkeypatch.delenv(env, raising=False)

    assert _detect_ai_terminal() is False

    for var, val in [
        ("CLAUDE_CODE", "1"),
        ("CODEX_SANDBOX", "seatbelt"),
        ("GEMINI_CLI", "1"),
        ("ANTIGRAVITY_CLI_ALIAS", "agy"),
    ]:
        monkeypatch.setenv(var, val)
        assert _detect_ai_terminal() is True
        monkeypatch.delenv(var, raising=False)
