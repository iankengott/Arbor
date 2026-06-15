from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from arbor.cli.branch_guard import on_base_branch, resolve_start_branch


class DummyConsole:
    def print(self, *args: object, **kwargs: object) -> None:
        pass


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, text=True)


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "README.md").write_text("test\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "initial")
    _git(tmp_path, "branch", "-M", "main")
    return tmp_path


def test_on_base_branch_detects_current_and_base(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    is_base, current, base = on_base_branch(repo, None)

    assert is_base is True
    assert current == "main"
    assert base == "main"


def test_noninteractive_non_base_branch_aborts_with_fix(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "coordinator/trunk")
    config = SimpleNamespace(base_branch=None, require_base_branch=True)

    result = resolve_start_branch(
        repo,
        config,
        allow_non_base=False,
        interactive=False,
        console=DummyConsole(),
    )

    captured = capsys.readouterr()
    assert result == "abort"
    assert config.require_base_branch is True
    assert "git checkout main" in captured.out


def test_allow_non_base_branch_disables_base_requirement(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "feature")
    config = SimpleNamespace(base_branch=None, require_base_branch=True)

    result = resolve_start_branch(
        repo,
        config,
        allow_non_base=True,
        interactive=False,
        console=DummyConsole(),
    )

    assert result == "proceed"
    assert config.require_base_branch is False
