"""`arbor init` — scaffold Arbor settings in a target project."""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

import typer


_COMMON_EVALS = (
    "eval.sh",
    "evaluate.sh",
    "run_eval.sh",
    "scripts/eval.sh",
    "scripts/evaluate.sh",
    "scripts/run_eval.sh",
    "eval.py",
    "evaluate.py",
    "run_eval.py",
    "scripts/eval.py",
    "scripts/evaluate.py",
    "scripts/run_eval.py",
)
_SCORE_RE = re.compile(r"(?:score|accuracy|metric|loss)\s*[:=]\s*(-?\d+(?:\.\d+)?)", re.I)


def init_command(
    cwd: Path = typer.Option(Path("."), "--cwd", help="Target project directory."),
    eval_cmd: str | None = typer.Option(None, "--eval-cmd", help="Command Arbor should run to score an attempt."),
    metric: str = typer.Option("score", "--metric", help="Metric name to optimize."),
    direction: str = typer.Option("maximize", "--direction", help="maximize or minimize."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite an existing arbor.yaml."),
    run_baseline: bool = typer.Option(False, "--run-baseline", help="Run the eval command once and report a parsed metric."),
) -> None:
    """Create a starter arbor.yaml and optionally validate the baseline command."""
    target = cwd.resolve()
    if not target.exists() or not target.is_dir():
        typer.secho(f"error: target directory does not exist: {target}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    config_path = target / "arbor.yaml"
    if config_path.exists() and not force:
        typer.secho(f"error: {config_path} already exists; pass --force to overwrite", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    if direction not in {"maximize", "minimize"}:
        typer.secho("error: --direction must be maximize or minimize", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    detected = eval_cmd or _detect_eval_command(target)
    protected = _detect_protected_paths(target)
    _write_config(config_path, detected, metric, direction, protected)

    typer.secho(f"wrote {config_path}", fg=typer.colors.GREEN)
    if detected:
        typer.echo(f"eval command: {detected}")
    else:
        typer.secho(
            "no common eval command found; edit arbor.yaml and fill in executor.experiment_cmd",
            fg=typer.colors.YELLOW,
        )
    if protected:
        typer.echo(f"protected paths: {', '.join(protected)}")

    if run_baseline:
        if not detected:
            typer.secho("cannot run baseline without an eval command", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2)
        _run_baseline(target, detected)

    typer.echo("\nNext:")
    typer.echo(f"  cd {target}")
    typer.echo("  arbor \"improve the metric without touching protected data\"")


def _detect_eval_command(target: Path) -> str | None:
    for rel in _COMMON_EVALS:
        path = target / rel
        if not path.is_file():
            continue
        quoted = shlex.quote(rel)
        if path.suffix == ".py":
            return f"python {quoted}"
        return f"bash {quoted}"
    return None


def _detect_protected_paths(target: Path) -> list[str]:
    candidates = ("data", "datasets", "eval_data", "test", "tests/fixtures")
    return [rel for rel in candidates if (target / rel).exists()]


def _write_config(
    path: Path,
    eval_cmd: str | None,
    metric: str,
    direction: str,
    protected_paths: list[str],
) -> None:
    experiment_cmd = eval_cmd or "TODO: replace with your evaluation command"
    protected_yaml = "\n".join(f"  - {p}" for p in protected_paths) or "  - data"
    path.write_text(
        "\n".join(
            [
                "task: >",
                f"  Improve the project {metric}. Do not modify evaluation code or protected data.",
                "",
                "metric:",
                f"  name: {metric}",
                f"  direction: {direction}",
                "",
                "protected_paths:",
                protected_yaml,
                "",
                "executor:",
                f"  experiment_cmd: {experiment_cmd!r}",
                "  max_turns: 50",
                "",
                "coordinator:",
                "  max_cycles: 5",
                "  max_depth: 2",
                "  merge_threshold: 0.01",
                "  ui:",
                "    interaction_mode: review",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _run_baseline(target: Path, eval_cmd: str) -> None:
    typer.echo("\nrunning baseline...")
    proc = subprocess.run(
        eval_cmd,
        cwd=target,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
        check=False,
    )
    output = proc.stdout.strip()
    if output:
        typer.echo(output[-4000:])
    if proc.returncode != 0:
        typer.secho(f"baseline command exited with {proc.returncode}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    match = _SCORE_RE.search(output)
    if match:
        typer.secho(f"parsed baseline metric: {match.group(1)}", fg=typer.colors.GREEN)
    else:
        typer.secho(
            "baseline ran, but no metric like 'score: 0.8123' was detected",
            fg=typer.colors.YELLOW,
        )
