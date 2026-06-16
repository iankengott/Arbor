"""Token-price helpers for planning Arbor run budgets.

Prices are USD per 1M tokens. They are intentionally data-only so the CLI,
dashboard, and reports can share one source later.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json

import yaml


@dataclass(frozen=True)
class ModelPrice:
    model: str
    input_per_mtok: float
    output_per_mtok: float
    cached_input_per_mtok: float | None = None
    cache_creation_per_mtok: float | None = None
    provider: str = ""
    source: str = ""
    notes: str = ""

    def normalized(self) -> "ModelPrice":
        return ModelPrice(
            model=self.model,
            input_per_mtok=self.input_per_mtok,
            output_per_mtok=self.output_per_mtok,
            cached_input_per_mtok=(
                self.cached_input_per_mtok
                if self.cached_input_per_mtok is not None
                else self.input_per_mtok
            ),
            cache_creation_per_mtok=(
                self.cache_creation_per_mtok
                if self.cache_creation_per_mtok is not None
                else self.input_per_mtok
            ),
            provider=self.provider,
            source=self.source,
            notes=self.notes,
        )


@dataclass(frozen=True)
class TokenEstimate:
    uncached_input_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    output_tokens: int

    @property
    def input_tokens(self) -> int:
        return self.uncached_input_tokens + self.cache_read_tokens + self.cache_creation_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class CostEstimate:
    price: ModelPrice
    tokens: TokenEstimate
    cost_usd: float


@dataclass(frozen=True)
class MagnonicsCostPlan:
    preset: str
    shape: dict[str, int]
    complexity_points: int
    notes: tuple[str, ...]


PRICING_LAST_VERIFIED = "2026-06-16"

_OPENAI_SOURCE = "OpenAI API pricing"
_ANTHROPIC_SOURCE = "Anthropic Claude model/pricing docs"

KNOWN_MODEL_PRICES: dict[str, ModelPrice] = {
    "gpt-5": ModelPrice("gpt-5", 1.25, 10.00, 0.125, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.5": ModelPrice("gpt-5.5", 2.50, 15.00, 0.25, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.5-long": ModelPrice("gpt-5.5-long", 5.00, 22.50, 0.50, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.5-pro": ModelPrice("gpt-5.5-pro", 15.00, 90.00, None, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.4": ModelPrice("gpt-5.4", 1.25, 7.50, 0.13, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.4-long": ModelPrice("gpt-5.4-long", 2.50, 11.25, 0.25, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.4-mini": ModelPrice("gpt-5.4-mini", 0.375, 2.25, 0.0375, provider="openai", source=_OPENAI_SOURCE),
    "gpt-5.4-nano": ModelPrice("gpt-5.4-nano", 0.10, 0.625, 0.01, provider="openai", source=_OPENAI_SOURCE),
    "claude-opus-4-8": ModelPrice("claude-opus-4-8", 5.00, 25.00, 0.50, 6.25, "anthropic", _ANTHROPIC_SOURCE),
    "claude-sonnet-4-6": ModelPrice("claude-sonnet-4-6", 3.00, 15.00, 0.30, 3.75, "anthropic", _ANTHROPIC_SOURCE),
    "claude-haiku-4-5": ModelPrice("claude-haiku-4-5", 1.00, 5.00, 0.10, 1.25, "anthropic", _ANTHROPIC_SOURCE),
}

MODEL_ALIASES: dict[str, str] = {
    "claude-sonnet-4-20250514": "claude-sonnet-4-6",
    "claude-sonnet-4-5": "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001": "claude-haiku-4-5",
    "claude-opus-4-8-20260212": "claude-opus-4-8",
}


def price_for_model(model: str) -> ModelPrice | None:
    key = (model or "").strip().lower()
    return KNOWN_MODEL_PRICES.get(key) or KNOWN_MODEL_PRICES.get(MODEL_ALIASES.get(key, ""))


def estimate_tokens_from_plan(
    *,
    cycles: int,
    executors_per_cycle: int,
    coordinator_turns_per_cycle: int,
    executor_turns: int,
    input_tokens_per_turn: int,
    output_tokens_per_turn: int,
    cache_read_ratio: float,
    cache_creation_ratio: float,
) -> TokenEstimate:
    turns = cycles * (coordinator_turns_per_cycle + executors_per_cycle * executor_turns)
    logical_input = max(0, turns * input_tokens_per_turn)
    cache_read = int(logical_input * max(0.0, min(cache_read_ratio, 1.0)))
    remaining = logical_input - cache_read
    cache_creation = int(remaining * max(0.0, min(cache_creation_ratio, 1.0)))
    uncached = max(0, logical_input - cache_read - cache_creation)
    output = max(0, turns * output_tokens_per_turn)
    return TokenEstimate(
        uncached_input_tokens=uncached,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_creation,
        output_tokens=output,
    )


def estimate_cost(price: ModelPrice, tokens: TokenEstimate) -> CostEstimate:
    p = price.normalized()
    cost = (
        tokens.uncached_input_tokens * p.input_per_mtok
        + tokens.cache_read_tokens * (p.cached_input_per_mtok or p.input_per_mtok)
        + tokens.cache_creation_tokens * (p.cache_creation_per_mtok or p.input_per_mtok)
        + tokens.output_tokens * p.output_per_mtok
    ) / 1_000_000
    return CostEstimate(price=p, tokens=tokens, cost_usd=cost)


def load_magnonics_cost_plan(path: str | Path, preset: str = "pilot") -> MagnonicsCostPlan:
    """Estimate a smoke/pilot/full Arbor run shape from a magnonics evaluator config."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise ValueError(f"magnonics config not found: {config_path}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"magnonics config must be a YAML mapping: {config_path}")

    root = config_path.parent.parent
    temperature_count = len(_csv_values(config.get("temperature_points_C"))) or 1
    fmr_count = len(_csv_values(config.get("fmr_field_points")))
    objective_count = len(config.get("objective_weights") or {})
    evidence_count = len(_csv_values(config.get("required_evidence")))
    literature_count = _count_markdown_files(root / str(config.get("literature_dir", "literature")))
    material_rows = _count_csv_rows(root / str(config.get("materials_database", "")))
    simulator_bonus = 2 if isinstance(config.get("simulator"), dict) else 0
    human_review_bonus = 2 if isinstance(config.get("human_review"), dict) else 0

    complexity_points = (
        temperature_count
        + fmr_count
        + objective_count
        + evidence_count
        + literature_count
        + min(material_rows, 12)
        + simulator_bonus
        + human_review_bonus
    )

    preset_key = _magnonics_preset_key(preset)
    base_input = 16_000 + complexity_points * 900
    base_output = 2_200 + complexity_points * 110
    if preset_key == "smoke":
        shape = {
            "cycles": 1,
            "executors_per_cycle": 1,
            "coordinator_turns_per_cycle": 3,
            "executor_turns": 8 + max(0, temperature_count - 1),
            "input_tokens_per_turn": max(18_000, int(base_input * 0.65)),
            "output_tokens_per_turn": max(2_500, int(base_output * 0.70)),
        }
    elif preset_key == "full":
        shape = {
            "cycles": max(6, min(12, 4 + complexity_points // 5)),
            "executors_per_cycle": 2 if literature_count + material_rows >= 6 else 1,
            "coordinator_turns_per_cycle": 7,
            "executor_turns": 36 + complexity_points // 2,
            "input_tokens_per_turn": int(base_input * 1.50),
            "output_tokens_per_turn": int(base_output * 1.35),
        }
    else:
        shape = {
            "cycles": max(3, min(6, 2 + literature_count // 2 + material_rows // 4)),
            "executors_per_cycle": 1,
            "coordinator_turns_per_cycle": 5,
            "executor_turns": 18 + temperature_count + fmr_count // 2 + literature_count // 2,
            "input_tokens_per_turn": base_input,
            "output_tokens_per_turn": base_output,
        }

    notes = (
        (
            f"config features: {temperature_count} temperature point(s), {fmr_count} FMR field point(s), "
            f"{literature_count} literature note(s), {material_rows} material database row(s)"
        ),
        f"complexity points: {complexity_points}",
        f"scope: {preset_key} magnonics plan includes evaluator context, candidate ranking, and review gates",
    )
    return MagnonicsCostPlan(preset=preset_key, shape=shape, complexity_points=complexity_points, notes=notes)


def load_usage_tokens(path: str | Path) -> TokenEstimate:
    """Read an Arbor events.jsonl file and sum LLM_CALL token fields."""
    uncached = cache_read = cache_creation = output = 0
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type") or event.get("event")
            data = event.get("data") if isinstance(event.get("data"), dict) else event
            if event_type and event_type != "llm.call":
                continue
            uncached += int(data.get("uncached_input_tokens") or data.get("input_tokens") or 0)
            cache_read += int(data.get("cache_read_tokens") or 0)
            cache_creation += int(data.get("cache_creation_tokens") or 0)
            output += int(data.get("output_tokens") or 0)
    return TokenEstimate(uncached, cache_read, cache_creation, output)


def _magnonics_preset_key(preset: str) -> str:
    key = (preset or "pilot").strip().lower()
    aliases = {
        "standard": "pilot",
        "deep": "full",
    }
    key = aliases.get(key, key)
    if key not in {"smoke", "pilot", "full"}:
        return "pilot"
    return key


def _csv_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _count_markdown_files(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    return len([item for item in path.iterdir() if item.is_file() and item.suffix.lower() == ".md"])


def _count_csv_rows(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for row in reader if any(value for value in row.values()))
