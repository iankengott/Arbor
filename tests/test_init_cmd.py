from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from arbor.cli.app import app


def test_init_detects_python_eval_and_writes_config(tmp_path: Path) -> None:
    (tmp_path / "eval.py").write_text("print('score: 0.5')\n", encoding="utf-8")
    (tmp_path / "data").mkdir()

    result = CliRunner().invoke(app, ["init", "--cwd", str(tmp_path)])

    assert result.exit_code == 0
    config = (tmp_path / "arbor.yaml").read_text(encoding="utf-8")
    assert "experiment_cmd: 'python eval.py'" in config
    assert "  - data" in config
    assert "wrote" in result.output


def test_init_run_baseline_parses_score(tmp_path: Path) -> None:
    (tmp_path / "eval.py").write_text("print('score: 0.75')\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["init", "--cwd", str(tmp_path), "--run-baseline"])

    assert result.exit_code == 0
    assert "parsed baseline metric: 0.75" in result.output


def test_init_does_not_overwrite_without_force(tmp_path: Path) -> None:
    (tmp_path / "arbor.yaml").write_text("existing\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["init", "--cwd", str(tmp_path)])

    assert result.exit_code == 2
    assert "already exists" in result.output
