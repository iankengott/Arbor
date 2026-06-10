# Configuration

Arbor reads configuration from several places. Understanding the precedence order makes
everything else predictable.

## Where configuration comes from

From highest priority to lowest:

1. **Command-line flags** — e.g. `--max-cycles`, `--mode`. Always win.
2. **Project config** — a YAML file in your target project (`research_config.yaml`,
   `arbor.yaml`, or `autoresearch.yaml`, auto-detected; or pass `--config PATH`).
3. **User config** — global defaults written by `arbor setup` (provider, model, API key).
4. **Plugin profile / overrides** — bundled defaults for a domain (see [Plugins](plugins.md)).
5. **Built-in defaults.**

!!! info "Rule of thumb"
    CLI overrides the project file, which overrides your global setup, which overrides a
    plugin profile. Set durable choices in config; use flags for one-off changes.

## A complete example

```yaml title="research_config.yaml"
# ── Model ──────────────────────────────────────────────
llm:
  provider: anthropic            # anthropic | openai | openai-compatible
  model: claude-sonnet-4-5
  api_key: ${ANTHROPIC_API_KEY}  # env vars are expanded
  base_url: null                 # set for OpenAI-compatible gateways
  reasoning_effort: medium       # low | medium | high (where supported)
  meta_model: null               # optional separate model for meta/distillation steps

# ── Orchestration ─────────────────────────────────────
max_cycles: 12                   # completed/skipped/failed experiments before finalizing
executor_max_turns: 60           # hard cap on a single executor's ReAct turns

# ── Timeouts (seconds) ────────────────────────────────
timeout:
  executor: 172800               # 48 h per experiment
  run_training_max: 604800       # 7 d ceiling for a single training command

# ── Human-in-the-loop & monitoring ────────────────────
ui:
  interaction_mode: auto         # auto | direction | review | collaborative
  webui_port: 8765               # read-only browser monitor
```

!!! note "Flat keys also work"
    Nested groups (`llm:`, `timeout:`, `ui:`) are the recommended style, but the
    equivalent flat keys are accepted too. See `examples/research_config.example.yaml` in
    the repository for an annotated reference.

## Providers

Arbor speaks to three families of backends. Pick one in the `llm:` block.

| `provider` | Use for | Notes |
| --- | --- | --- |
| `anthropic` | Claude models | Native Anthropic API. |
| `openai` | OpenAI models | Uses the Responses API for reasoning models. |
| `openai-compatible` | DeepSeek, Gemini, Qwen, vLLM, Ollama, local gateways | Routes through LiteLLM. Set `base_url`. |

=== "Anthropic"

    ```yaml
    llm:
      provider: anthropic
      model: claude-sonnet-4-5
      api_key: ${ANTHROPIC_API_KEY}
    ```

=== "OpenAI"

    ```yaml
    llm:
      provider: openai
      model: gpt-5
      api_key: ${OPENAI_API_KEY}
      reasoning_effort: medium
    ```

=== "OpenAI-compatible"

    ```yaml
    llm:
      provider: openai-compatible
      model: deepseek-chat
      api_key: ${OPENAI_API_KEY}
      base_url: https://your-gateway/v1
    ```

!!! tip "Keep keys out of files"
    Reference environment variables (`${ANTHROPIC_API_KEY}`) rather than pasting secrets
    into config. `arbor setup` stores your global key in the user config directory.

### `meta_model`

Some steps — distilling insight, drafting the report — don't need your most expensive
model. Set `meta_model` to route those meta-level calls to a cheaper or faster model while
the main reasoning loop uses `model`.

## Orchestration

| Key | Meaning |
| --- | --- |
| `max_cycles` | Maximum number of completed / skipped / failed idea experiments before Arbor finalizes and writes the report. Override per-run with `--max-cycles`. |
| `executor_max_turns` | Hard cap on a single executor's ReAct turns — a runaway/cost safety valve. Override with `--max-turns`. |

## Budgets and timeouts

The `timeout:` group bounds how long individual operations may run (in seconds):

| Key | Default | Meaning |
| --- | --- | --- |
| `executor` | `172800` (48 h) | Wall-clock limit for one experiment. |
| `run_training_max` | `604800` (7 d) | Ceiling for a single long-running training command. |

For benchmarks, the most convenient way to set a coherent budget is a **plugin profile**,
which bundles `max_cycles`, tree depth, executor timeout, and total time budget under one
name (e.g. `mle_bench_lite`). See [Plugins](plugins.md).

## Human-in-the-loop & monitoring

The `ui:` group controls oversight and the live monitor:

| Key | Meaning |
| --- | --- |
| `interaction_mode` | `auto`, `direction`, `review`, or `collaborative`. See [Interaction Modes](interaction-modes.md). Override with `--mode`. |
| `webui_port` | Port for the browser monitor (default `8765`). See [Web UI & Monitoring](web-ui.md). Override with `--webui-port`; disable with `--no-webui`. |

## Plugins & domain targeting

Two top-level keys retarget Arbor to a domain without touching code:

```yaml
plugin: mle_kaggle              # load a bundled domain plugin
plugin_profile: mle_bench_lite  # pick a named budget/behaviour profile within it
```

See [Plugins](plugins.md) for the full plugin format and the built-in `mle_kaggle` plugin.

## Inspecting config

```bash
arbor config        # inspect/manage stored configuration
arbor doctor        # verify provider keys and environment are usable
```
