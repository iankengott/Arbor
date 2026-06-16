"""`arbor demo` — run an offline confidence-check dashboard."""

from __future__ import annotations

import time
import subprocess
from pathlib import Path

import typer


def demo_command(
    rounds: int = typer.Option(2, "--rounds", "-r", min=1, help="Number of mock cycles to replay."),
    webui_port: int | None = typer.Option(8765, "--webui-port", help="Read-only WebUI port."),
    no_webui: bool = typer.Option(False, "--no-webui", help="Run the terminal demo only."),
    benchmark: str = typer.Option("none", "--benchmark", help="Run a bundled benchmark first: none, hello, or magnonics."),
) -> None:
    """Replay a complete Arbor run without API keys, model calls, or project setup."""
    from ...cli.run_dashboard import RunDashboard
    from ...cli.run_state import RunState
    from ...events import EventBus
    from ...events.mock import emit_mock_run

    if benchmark != "none":
        _run_benchmark_demo(benchmark)

    bus = EventBus()
    state = RunState(
        run_name="offline_demo",
        task="Improve validation accuracy",
        cwd=str(Path.cwd()),
        model="offline-mock-model",
        total_cycles=3,
    )

    webui = None
    if not no_webui and webui_port is not None:
        from ...webui import WebUIServer

        webui = WebUIServer(state, bus, port=webui_port)
        if webui.start():
            typer.secho(f"\nWebUI: {webui.url}", fg=typer.colors.CYAN)
            typer.echo("Open it now if you want to watch the browser monitor.")
            time.sleep(2)
        else:
            typer.secho(
                f"\nCould not bind WebUI port {webui_port}; continuing terminal-only.",
                fg=typer.colors.YELLOW,
            )
            webui = None

    try:
        with RunDashboard(state, bus, enable_input=False):
            for _ in range(rounds):
                emit_mock_run(bus, delay=0.25)
            time.sleep(2)
    finally:
        if webui is not None:
            webui.stop()

    verified = "local CLI, dashboard, and events"
    if not no_webui:
        verified += "; WebUI started when a port was available"
    typer.secho(f"\nDemo complete. This verified the {verified}.", fg=typer.colors.GREEN)


def _run_benchmark_demo(name: str) -> None:
    repo_root = _repo_root()
    benchmarks = {
        "hello": (
            repo_root / "examples" / "hello_benchmark",
            ["python", "eval.py"],
        ),
        "magnonics": (
            repo_root / "examples" / "magnonics_benchmark",
            ["python", "scripts/evaluate.py", "--config", "configs/example.yaml"],
        ),
    }
    if name not in benchmarks:
        typer.secho("error: --benchmark must be none, hello, or magnonics", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    cwd, cmd = benchmarks[name]
    if not cwd.exists():
        typer.secho(f"error: bundled benchmark not found: {cwd}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    typer.secho(f"\nRunning {name} benchmark evaluator", fg=typer.colors.CYAN, bold=True)
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    typer.echo(proc.stdout.rstrip())
    if proc.returncode != 0:
        raise typer.Exit(code=proc.returncode)
    if name == "magnonics":
        typer.echo(f"metrics: {cwd / 'outputs' / 'metrics.json'}")
        typer.echo(f"scenario: {cwd / 'scenario' / 'arena_lab_inspired.yaml'}")


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "examples").is_dir():
            return parent
    return Path.cwd()
