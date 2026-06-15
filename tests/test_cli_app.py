from __future__ import annotations

import sys
from typing import Callable

import pytest

from arbor.cli import app as cli_app


def test_main_defaults_to_run_for_root_options(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake_app() -> None:
        seen.append(list(sys.argv))

    monkeypatch.setattr(cli_app, "app", fake_app)
    monkeypatch.setattr(sys, "argv", ["arbor", "--cwd", "."])

    cli_app.main()

    assert seen == [["arbor", "run", "--cwd", "."]]


def test_main_maps_version_flag_to_version_command(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake_app() -> None:
        seen.append(list(sys.argv))

    monkeypatch.setattr(cli_app, "app", fake_app)
    monkeypatch.setattr(sys, "argv", ["arbor", "--version"])

    cli_app.main()

    assert seen == [["arbor", "version"]]


def test_main_suggests_close_unknown_command(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    called = False

    def fake_app() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(cli_app, "app", fake_app)
    monkeypatch.setattr(sys, "argv", ["arbor", "docter"])

    with pytest.raises(SystemExit) as exc:
        cli_app.main()

    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert called is False
    assert "Did you mean 'doctor'?" in captured.err
