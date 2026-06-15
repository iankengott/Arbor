from __future__ import annotations

from pathlib import Path

from arbor.coordinator.orchestrator import _source_tree_root


def test_source_tree_root_tracks_standard_src_layout() -> None:
    root = _source_tree_root()

    assert root is not None
    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "arbor").is_dir()
    assert root == Path(__file__).resolve().parents[1]
