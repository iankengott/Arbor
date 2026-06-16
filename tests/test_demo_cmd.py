from __future__ import annotations

from pathlib import Path

from arbor.cli.commands.demo_cmd import _repo_root, _run_benchmark_demo


def test_repo_root_detects_flat_src_layout() -> None:
    root = _repo_root()

    assert root == Path(__file__).resolve().parents[1]
    assert (root / "examples" / "hello_benchmark").is_dir()


def test_bundled_hello_benchmark_runs(capsys) -> None:
    _run_benchmark_demo("hello")

    captured = capsys.readouterr()
    assert "Running hello benchmark evaluator" in captured.out
    assert "score:" in captured.out
