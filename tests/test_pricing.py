from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from arbor.cli.app import app
from arbor.core.pricing import (
    ModelPrice,
    TokenEstimate,
    estimate_cost,
    estimate_tokens_from_plan,
    load_magnonics_cost_plan,
    load_usage_tokens,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MAGNONICS_CONFIG = REPO_ROOT / "examples" / "magnonics_benchmark" / "configs" / "example.yaml"


def test_estimate_cost_uses_cache_prices() -> None:
    price = ModelPrice("custom", input_per_mtok=10, output_per_mtok=20, cached_input_per_mtok=1, cache_creation_per_mtok=12)
    tokens = TokenEstimate(uncached_input_tokens=100_000, cache_read_tokens=200_000, cache_creation_tokens=50_000, output_tokens=10_000)

    estimate = estimate_cost(price, tokens)

    assert round(estimate.cost_usd, 2) == 2.00


def test_estimate_tokens_from_plan_counts_all_turns() -> None:
    tokens = estimate_tokens_from_plan(
        cycles=2,
        executors_per_cycle=1,
        coordinator_turns_per_cycle=2,
        executor_turns=3,
        input_tokens_per_turn=1000,
        output_tokens_per_turn=100,
        cache_read_ratio=0.5,
        cache_creation_ratio=0.1,
    )

    assert tokens.input_tokens == 10_000
    assert tokens.cache_read_tokens == 5_000
    assert tokens.cache_creation_tokens == 500
    assert tokens.uncached_input_tokens == 4_500
    assert tokens.output_tokens == 1_000


def test_load_usage_tokens_reads_events_jsonl(tmp_path: Path) -> None:
    usage = tmp_path / "events.jsonl"
    usage.write_text(
        '{"type":"llm.call","data":{"uncached_input_tokens":100,"cache_read_tokens":20,"cache_creation_tokens":10,"output_tokens":5}}\n'
        '{"type":"tool.start","data":{}}\n',
        encoding="utf-8",
    )

    tokens = load_usage_tokens(usage)

    assert tokens.uncached_input_tokens == 100
    assert tokens.cache_read_tokens == 20
    assert tokens.cache_creation_tokens == 10
    assert tokens.output_tokens == 5


def test_cost_command_accepts_custom_prices() -> None:
    result = CliRunner().invoke(
        app,
        [
            "cost",
            "--model",
            "local-model",
            "--input-price",
            "1",
            "--output-price",
            "2",
            "--cycles",
            "1",
            "--coordinator-turns-per-cycle",
            "1",
            "--executor-turns",
            "1",
            "--input-tokens-per-turn",
            "1000",
            "--output-tokens-per-turn",
            "1000",
        ],
    )

    assert result.exit_code == 0
    assert "estimated LLM cost" in result.output
    assert "local-model" in result.output


def test_cost_command_shape_label_reflects_overrides() -> None:
    result = CliRunner().invoke(
        app,
        [
            "cost",
            "--model",
            "local-model",
            "--input-price",
            "1",
            "--output-price",
            "2",
            "--cycles",
            "1",
            "--executors-per-cycle",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "shape: standard plan: 1 cycles, 3 executor(s)/cycle" in result.output
    assert "shape: standard plan: 8 cycles" not in result.output


def test_magnonics_cost_plan_reads_config_features() -> None:
    plan = load_magnonics_cost_plan(MAGNONICS_CONFIG, preset="pilot")

    assert plan.preset == "pilot"
    assert plan.shape["cycles"] >= 3
    assert plan.shape["executor_turns"] > 18
    assert plan.shape["input_tokens_per_turn"] > 16_000
    assert plan.complexity_points >= 20
    assert any("temperature point" in note for note in plan.notes)
    assert any("material database row" in note for note in plan.notes)


def test_cost_command_estimates_magnonics_config() -> None:
    result = CliRunner().invoke(
        app,
        [
            "cost",
            "--model",
            "local-model",
            "--input-price",
            "1",
            "--output-price",
            "2",
            "--magnonics-config",
            str(MAGNONICS_CONFIG),
            "--preset",
            "full",
        ],
    )

    assert result.exit_code == 0
    assert "full magnonics plan" in result.output
    assert "magnonics config:" in result.output
    assert "temperature point" in result.output
    assert "estimated LLM cost" in result.output
