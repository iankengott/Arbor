from __future__ import annotations

from pathlib import Path

import click
import pytest

from arbor.cli.commands import doctor_cmd


def test_doctor_reports_setup_needed_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(doctor_cmd, "GLOBAL_CONFIG_FILE", tmp_path / "missing-config.yaml")
    monkeypatch.setattr(doctor_cmd, "LEGACY_GLOBAL_CONFIG_FILE", tmp_path / "missing-legacy.yaml")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(doctor_cmd.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None)
    monkeypatch.setattr(
        doctor_cmd.subprocess,
        "check_output",
        lambda *args, **kwargs: "git version 2.0.0",
    )
    monkeypatch.setattr(doctor_cmd.sys, "argv", ["arbor"])

    with pytest.raises(click.exceptions.Exit) as exc:
        doctor_cmd.doctor_command()

    captured = capsys.readouterr()
    assert exc.value.exit_code == 1
    assert "install checks passed; setup still needed" in captured.out
