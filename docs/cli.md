# CLI Reference

Arbor installs the `arbor` command (plus a few lower-level entry points). This page is the
complete reference.

## Commands

| Command | What it does |
| --- | --- |
| `arbor` | With no subcommand, behaves like `arbor run` — starts an interactive session in the current directory. |
| `arbor run` | Start an AI-powered research session. |
| `arbor setup` | Interactive wizard to write your provider, model, and API key. |
| `arbor demo` | Replay an offline run through the dashboard/WebUI without API keys. |
| `arbor init` | Create a starter `arbor.yaml` in a target project and optionally run its baseline. |
| `arbor cost` | Estimate LLM spend from a planned run shape or existing events file. |
| `arbor config` | Inspect and manage stored configuration. |
| `arbor doctor` | Diagnose your environment (PATH, Python, git, API keys). |
| `arbor report` | Work with a finished run's report. |
| `arbor version` | Print the installed version. |

!!! tip
    Running `arbor` (or `arbor --cwd .`) with no subcommand is equivalent to `arbor run`.

## `arbor run`

```bash
arbor run [INSTRUCTION] [OPTIONS]
```

`INSTRUCTION` is an optional research-goal seed (e.g. `"maximize dev score without
changing eval or data"`). Omit it to start with the intake chat.

### Default flow

1. Open an interactive chat with the intake agent.
2. The agent confirms which project directory to work on (the `--cwd` flag is only a hint).
3. When you agree on a plan, the agent launches the experiment.
4. You confirm the research contract shown in the terminal.
5. A quick preflight runs against the chosen project.
6. The coordinator runs to completion and writes `REPORT.md`.

### Options

| Option | Description |
| --- | --- |
| `--cwd PATH` | Project directory hint. Intake verifies/adjusts it unless `--yes` is used. Default `.`. |
| `--config, -c PATH` | Project YAML config. Defaults to `research_config.yaml` / `arbor.yaml` / `autoresearch.yaml` in the target project. |
| `--max-cycles N` | Max completed/skipped/failed idea experiments before finalizing. |
| `--max-turns N` | Hard cap on coordinator ReAct turns — a cost/runaway safety valve. |
| `--intake-max-turns N` | Max planning-chat turns before launch (default `30`). |
| `--run-name NAME` | Session name under `.arbor/sessions/`. Defaults to a timestamp. |
| `--resume` | Resume an interrupted run from its checkpoint in the existing workspace/session. |
| `--workspace-dir PATH` | Session/artifact directory override. Default `<target>/.arbor/sessions/<run_name>`. |
| `--verbose, -v` | Show lower-level coordinator logs. |
| `--yes-cwd PATH` | Target project directory when `--yes` skips intake. Required with `--yes`. |
| `--yes, -y` | Skip intake chat and launch directly from instruction + `--yes-cwd`. |
| `--no-dashboard-input` | Disable live terminal input; prompts/review gates auto-continue after timeout. |
| `--followup / --no-followup` | After `REPORT.md`, open a read-only Q&A prompt about the finished run (default on). |
| `--verbose-preflight` | Print successful preflight checks too (default shows only failures/warnings). |
| `--webui-port N` | Read-only browser monitor port. Default auto-starts near `8765` for interactive runs. |
| `--no-webui` | Do not start the read-only browser monitor. |
| `--interaction-mode, --mode MODE` | Human-in-loop mode: `auto`, `direction`, `review`, `collaborative`. |
| `--allow-non-base-branch` | Allow starting from the current non-`main` branch. Useful for dev, risky for benchmarks. |

### Examples

```bash
# Interactive: chat with intake, then run in the current directory
arbor run

# Seed a goal, still go through intake
arbor run "improve held-out accuracy"

# Headless: skip the chat entirely
arbor run "maximize the competition metric" \
  --yes --yes-cwd /path/to/project \
  --config /path/to/project/research_config.yaml

# Ask for approval before each idea is run
arbor run --mode review

# Resume an interrupted session
arbor run --resume --run-name my-study
```

## Interactive slash commands

While a run is active, type these in the terminal dashboard. A short menu pops up as you
type `/`; `/help` lists them all.

| Command | Action |
| --- | --- |
| `/help` | Show all dashboard commands. |
| `/ask <question>` | Ask the read-only companion a question about the run. |
| `/steer <message>` | Inject a message into the research agent. |
| `/mode ask\|research` | Set the default target for plain input. |
| `/status` | Print run status. |
| `/skill <name...>` | Ask the agent to load the named skill(s). |
| `/tree` | Print the current Idea Tree snapshot. |
| `/evidence` | Show score/baseline evidence. |
| `/reply` | Expand/collapse the full companion answer (or press ++tab++). |
| `/chart` | Toggle the live progress chart. |
| `/branches` | Show explored branch refs. |
| `/cost` | Print token usage. |
| `/pause` | Ask the agent to pause after the current step. |
| `/resume` | Resume after `/pause`. |
| `/report` | Show session/report artifact paths. |
| `/abort` (or `/quit`) | Abort the run. |

## Other entry points

For advanced/low-level use, Arbor also installs:

| Command | Purpose |
| --- | --- |
| `executor` | Run a single executor directly. |
| `coordinator` | Run the coordinator directly. |
| `run-research` | Lower-level run entry point. |
| `review-research` | Review a finished run. |

Most users only need `arbor`.

## Onboarding helpers

```bash
arbor demo
arbor demo --benchmark magnonics --no-webui --rounds 1
arbor init --cwd ./my_project --run-baseline
arbor cost --model claude-sonnet-4-6 --preset standard
```

`arbor demo` is the fastest no-risk check after installation. `arbor init` is optional,
but useful when you want a reusable project config before running intake; pass
`--eval-cmd "bash eval.sh"` if your evaluation command is not one of the common names.

`arbor cost` includes a small built-in pricing table for common OpenAI and Anthropic
models plus custom prices for private gateways:

```bash
arbor cost --list-models
arbor cost --model gpt-5 --preset smoke
arbor cost --model local-gateway --input-price 0.20 --output-price 0.80
arbor cost --model claude-sonnet-4-6 --usage-file .arbor/sessions/run/events.jsonl
arbor cost --model claude-sonnet-4-6 --magnonics-config examples/magnonics_benchmark/configs/example.yaml --preset full
```

The estimate is a planning tool, not a bill. It cannot know future retries, exact context
growth, cache hit rate, output verbosity, provider-side routing, or price changes.
