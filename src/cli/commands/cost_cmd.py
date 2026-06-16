"""`arbor cost` — estimate token spend before or after a run."""

from __future__ import annotations

from pathlib import Path

import typer

from ...core.pricing import (
    KNOWN_MODEL_PRICES,
    PRICING_LAST_VERIFIED,
    ModelPrice,
    estimate_cost,
    estimate_tokens_from_plan,
    load_magnonics_cost_plan,
    load_usage_tokens,
    price_for_model,
)


_PRESETS = {
    "smoke": {
        "cycles": 2,
        "executors_per_cycle": 1,
        "coordinator_turns_per_cycle": 4,
        "executor_turns": 8,
        "input_tokens_per_turn": 18_000,
        "output_tokens_per_turn": 2_500,
    },
    "standard": {
        "cycles": 8,
        "executors_per_cycle": 1,
        "coordinator_turns_per_cycle": 6,
        "executor_turns": 30,
        "input_tokens_per_turn": 35_000,
        "output_tokens_per_turn": 4_000,
    },
    "deep": {
        "cycles": 20,
        "executors_per_cycle": 2,
        "coordinator_turns_per_cycle": 8,
        "executor_turns": 60,
        "input_tokens_per_turn": 60_000,
        "output_tokens_per_turn": 6_000,
    },
}


def cost_command(
    model: str = typer.Option("claude-sonnet-4-6", "--model", "-m", help="Known model name, alias, or custom label."),
    preset: str = typer.Option("standard", "--preset", help="smoke, standard, or deep run shape; smoke, pilot, or full with --magnonics-config."),
    cycles: int | None = typer.Option(None, "--cycles", help="Override cycles in the preset."),
    executors_per_cycle: int | None = typer.Option(None, "--executors-per-cycle", help="Executor branches per cycle."),
    coordinator_turns_per_cycle: int | None = typer.Option(None, "--coordinator-turns-per-cycle", help="Coordinator turns per cycle."),
    executor_turns: int | None = typer.Option(None, "--executor-turns", help="Executor turns per branch."),
    input_tokens_per_turn: int | None = typer.Option(None, "--input-tokens-per-turn", help="Average logical input tokens per LLM call."),
    output_tokens_per_turn: int | None = typer.Option(None, "--output-tokens-per-turn", help="Average output tokens per LLM call."),
    cache_read_ratio: float = typer.Option(0.35, "--cache-read-ratio", min=0.0, max=1.0, help="Share of input tokens billed as cache reads."),
    cache_creation_ratio: float = typer.Option(0.05, "--cache-creation-ratio", min=0.0, max=1.0, help="Share of non-read input tokens billed as cache writes."),
    usage_file: Path | None = typer.Option(None, "--usage-file", help="Estimate from an Arbor events.jsonl file instead of a plan."),
    magnonics_config: Path | None = typer.Option(None, "--magnonics-config", help="Estimate smoke/pilot/full run shapes from a magnonics evaluator config."),
    input_price: float | None = typer.Option(None, "--input-price", help="Custom uncached input price per 1M tokens."),
    output_price: float | None = typer.Option(None, "--output-price", help="Custom output price per 1M tokens."),
    cached_input_price: float | None = typer.Option(None, "--cached-input-price", help="Custom cached-input/read price per 1M tokens."),
    cache_creation_price: float | None = typer.Option(None, "--cache-creation-price", help="Custom cache-write price per 1M tokens."),
    list_models: bool = typer.Option(False, "--list-models", help="List built-in pricing table and exit."),
) -> None:
    """Estimate Arbor LLM spend. This is a planning range, not a billing guarantee."""
    if list_models:
        _print_models()
        return
    if usage_file is not None and magnonics_config is not None:
        typer.secho("--usage-file and --magnonics-config cannot be used together", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    price = _resolve_price(
        model=model,
        input_price=input_price,
        output_price=output_price,
        cached_input_price=cached_input_price,
        cache_creation_price=cache_creation_price,
    )
    if price is None:
        typer.secho(
            "unknown model price; pass --input-price and --output-price, or run --list-models",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    if usage_file is not None:
        tokens = load_usage_tokens(usage_file)
        shape_label = f"actual usage from {usage_file}"
        plan_notes: tuple[str, ...] = ()
    else:
        if magnonics_config is not None:
            try:
                magnonics_plan = load_magnonics_cost_plan(magnonics_config, preset=preset)
            except ValueError as exc:
                typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
                raise typer.Exit(code=2) from exc
            shape = dict(magnonics_plan.shape)
            shape_name = f"{magnonics_plan.preset} magnonics plan"
            plan_notes = (f"magnonics config: {magnonics_config}",) + magnonics_plan.notes
        else:
            shape = dict(_PRESETS.get(preset, _PRESETS["standard"]))
            shape_name = f"{preset if preset in _PRESETS else 'standard'} plan"
            plan_notes = ()
        overrides = {
            "cycles": cycles,
            "executors_per_cycle": executors_per_cycle,
            "coordinator_turns_per_cycle": coordinator_turns_per_cycle,
            "executor_turns": executor_turns,
            "input_tokens_per_turn": input_tokens_per_turn,
            "output_tokens_per_turn": output_tokens_per_turn,
        }
        for key, value in overrides.items():
            if value is not None:
                shape[key] = value
        shape_label = (
            f"{shape_name}: "
            f"{shape['cycles']} cycles, {shape['executors_per_cycle']} executor(s)/cycle"
        )
        tokens = estimate_tokens_from_plan(
            **shape,
            cache_read_ratio=cache_read_ratio,
            cache_creation_ratio=cache_creation_ratio,
        )

    estimate = estimate_cost(price, tokens)
    p = estimate.price

    typer.secho("\nArbor cost estimate", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"model: {p.model} ({p.provider or 'custom'})")
    typer.echo(f"shape: {shape_label}")
    for note in plan_notes:
        typer.echo(note)
    typer.echo(f"pricing last verified: {PRICING_LAST_VERIFIED}")
    if p.source:
        typer.echo(f"source: {p.source}")
    typer.echo()
    typer.echo(f"uncached input: {tokens.uncached_input_tokens:,} tokens @ ${p.input_per_mtok:g}/M")
    typer.echo(f"cache reads:     {tokens.cache_read_tokens:,} tokens @ ${p.cached_input_per_mtok:g}/M")
    typer.echo(f"cache writes:    {tokens.cache_creation_tokens:,} tokens @ ${p.cache_creation_per_mtok:g}/M")
    typer.echo(f"output:          {tokens.output_tokens:,} tokens @ ${p.output_per_mtok:g}/M")
    typer.secho(f"\nestimated LLM cost: ${estimate.cost_usd:,.2f}", fg=typer.colors.GREEN, bold=True)
    typer.echo(
        "\nReliability: medium for rough budgeting, low for exact billing. Real cost changes with "
        "actual turns, retries, context growth, cache hit rate, routing, tool behavior, and provider pricing."
    )


def _resolve_price(
    *,
    model: str,
    input_price: float | None,
    output_price: float | None,
    cached_input_price: float | None,
    cache_creation_price: float | None,
) -> ModelPrice | None:
    if input_price is not None or output_price is not None:
        if input_price is None or output_price is None:
            typer.secho("--input-price and --output-price must be provided together", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2)
        return ModelPrice(
            model=model,
            input_per_mtok=input_price,
            output_per_mtok=output_price,
            cached_input_per_mtok=cached_input_price,
            cache_creation_per_mtok=cache_creation_price,
            provider="custom",
            source="user-supplied",
        )
    return price_for_model(model)


def _print_models() -> None:
    typer.secho(f"Known model prices (USD per 1M tokens, verified {PRICING_LAST_VERIFIED})", bold=True)
    for name in sorted(KNOWN_MODEL_PRICES):
        p = KNOWN_MODEL_PRICES[name].normalized()
        typer.echo(
            f"{name:<24} input ${p.input_per_mtok:<6g} "
            f"cached ${p.cached_input_per_mtok:<6g} "
            f"cache-write ${p.cache_creation_per_mtok:<6g} "
            f"output ${p.output_per_mtok:<6g}"
        )
