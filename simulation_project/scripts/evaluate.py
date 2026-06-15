from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def evaluate(config_path: Path) -> dict:
    config = yaml.safe_load(config_path.read_text()) or {}
    material = config.get("inputs", {}).get("material_formula", "unknown")

    # Placeholder deterministic score. Replace this with a real simulation
    # pipeline once the first target workflow is chosen.
    score = 1.0 if material else 0.0
    return {
        "score": score,
        "material_formula": material,
        "status": "placeholder",
        "notes": "Replace scripts/evaluate.py with the real simulation metric.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/example.yaml")
    args = parser.parse_args()

    metrics = evaluate(Path(args.config))
    output = Path("outputs/metrics.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
