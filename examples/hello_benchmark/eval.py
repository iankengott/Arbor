from __future__ import annotations

from pathlib import Path


def main() -> None:
    candidate = Path("solution.txt")
    text = candidate.read_text(encoding="utf-8").lower() if candidate.exists() else ""
    score = 0.50
    if "arbor" in text:
        score += 0.20
    if "evidence" in text:
        score += 0.20
    if "hypothesis" in text:
        score += 0.10
    print(f"score: {score:.2f}")


if __name__ == "__main__":
    main()
