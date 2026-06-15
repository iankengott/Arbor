from __future__ import annotations

from pathlib import Path

import pytest

from arbor.coordinator.idea_tree import IdeaTree, Node


def _tree(tmp_path: Path) -> IdeaTree:
    return IdeaTree(
        root=Node(id="ROOT", parent_id=None, hypothesis="Improve metric"),
        json_path=tmp_path / "idea_tree.json",
        md_path=tmp_path / "idea_tree.md",
        max_depth=2,
    )


def test_add_update_save_and_load_round_trip(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    child = Node(id=tree.next_child_id("ROOT"), parent_id="ROOT", depth=1, hypothesis="Try calibration")

    tree.add_node(child)
    tree.update_node("1", status="done", score=72.5, insight="Calibration helped", code_ref="arbor/1")
    loaded = IdeaTree.load_json(tmp_path / "idea_tree.json")

    assert loaded.get_root().hypothesis == "Improve metric"
    assert loaded.get_node("1") is not None
    assert loaded.get_node("1").status == "done"
    assert loaded.get_node("1").score == 72.5
    assert loaded.get_children("ROOT")[0].id == "1"
    assert "Calibration helped" in (tmp_path / "idea_tree.md").read_text(encoding="utf-8")


def test_next_child_id_skips_non_matching_child_ids(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    tree.add_node(Node(id="1", parent_id="ROOT", depth=1))
    tree.add_node(Node(id="notes", parent_id="ROOT", depth=1))
    tree.add_node(Node(id="1.1", parent_id="1", depth=2))

    assert tree.next_child_id("ROOT") == "2"
    assert tree.next_child_id("1") == "1.2"


def test_best_done_node_respects_metric_direction(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    tree.add_node(Node(id="1", parent_id="ROOT", depth=1, status="done", score=10.0))
    tree.add_node(Node(id="2", parent_id="ROOT", depth=1, status="merged", score=7.5))

    assert tree.get_best_done_node().id == "1"

    tree.meta["metric_direction"] = "minimize"

    assert tree.get_best_done_node().id == "2"
    assert tree.is_improvement(6.0, 7.0) is True
    assert tree.is_improvement(8.0, 7.0) is False


def test_update_node_rejects_unknown_fields(tmp_path: Path) -> None:
    tree = _tree(tmp_path)

    with pytest.raises(ValueError, match="Invalid field"):
        tree.update_node("ROOT", children_ids=["1"])


def test_prune_node_prunes_descendants_and_records_reason(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    tree.add_node(Node(id="1", parent_id="ROOT", depth=1))
    tree.add_node(Node(id="1.1", parent_id="1", depth=2))

    tree.prune_node("1", "overfits dev")

    assert tree.get_node("1").status == "pruned"
    assert tree.get_node("1.1").status == "pruned"
    assert "overfits dev" in tree.get_node("1").insight
