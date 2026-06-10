# Plugins

A plugin retargets Arbor to a **domain** without changing any code. It is a single YAML
file that declares how to evaluate work, what must stay protected, what outputs are
required, a compute budget, and some domain guidance for the agents.

You only need a plugin when you run the **same kind of benchmark repeatedly** and want
every run to use identical settings. For a one-off task you don't need one — just prepare a
repo and launch `arbor` (see [Preparing a Benchmark](preparing-a-benchmark.md)).

## Activating a plugin

Put one line in your project's config (`research_config.yaml`, `arbor.yaml`, or
`autoresearch.yaml`), then launch the interactive CLI from the project directory:

```yaml title="research_config.yaml"
plugin: mle_kaggle        # the only line that switches domains
```

```bash
cd my_competition
arbor
```

Arbor auto-discovers the config in the project directory; the intake chat then runs with
the plugin's contract and guidance already applied.

## The plugin format

Every plugin follows the **same standard shape**. A minimal one needs only a name and an
eval contract:

```yaml title="minimal_plugin.yaml"
name: my_domain
description: "One line on what this plugin optimizes"
schema_version: 1

eval_contract:
  metric_direction: maximize          # or: minimize
  eval_cmd: "bash {cwd}/eval.sh"      # {cwd} -> project directory
```

Everything else is optional and layered on top. The full set of fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | ✓ | Plugin identifier, referenced by `plugin:` in config. |
| `description` | ✓ | One-line summary shown in `arbor` plugin listings. |
| `schema_version` |  | Format version (currently `1`). |
| `eval_contract` | ✓ | How to score: `metric_direction`, `eval_cmd` (with `{cwd}` substitution), and optional `submission_path` / `sample_submission_path`. |
| `protected_paths` |  | Glob patterns that are read-only to executors — your data and harness. |
| `required_outputs` |  | Artifacts that must exist for a run to count as valid. |
| `profiles` |  | Named budget bundles (`max_cycles`, `max_tree_depth`, `executor_timeout`, `time_budget`), selected with `plugin_profile`. |
| `config_overrides` |  | Default config values the plugin sets for every run. |
| Prompt injections |  | Domain guidance merged into the agents' system prompts (see below). |

### Prompt injection points

Domain guidance is added at six well-defined points — four for the **coordinator** (the
research director) and two for the **executor** (the engineer that runs one experiment):

| Key | Injected into |
| --- | --- |
| `meta_preamble_inject` | Top of the coordinator prompt — overall objective and strategy. |
| `meta_init_inject` | Coordinator's discovery/setup phase. |
| `meta_ideate_inject` | Coordinator's idea-generation phase. |
| `meta_decide_inject` | Coordinator's merge/keep-or-prune decisions. |
| `sub_preamble_inject` | Top of the executor prompt. |
| `sub_workflow_inject` | Executor's workflow rules and guardrails. |

Each is plain markdown text. Use them to encode domain habits ("always produce a valid
baseline first", "never write to `data/`"), not to script a specific solution.

### Where each setting wins

Settings combine in a fixed priority order, lowest to highest:

```text
built-in defaults  <  plugin.config_overrides  <  profiles[active]  <  your YAML config  <  CLI flags
```

So a value you set in your own config always beats the plugin, and a CLI flag beats
everything.

## The bundled example: `mle_kaggle`

Arbor ships one plugin, `mle_kaggle`, as a complete worked example for Kaggle / MLE-bench
competitions. It declares the eval contract, protects the data and harness, requires a
`submission.csv`, and bundles a benchmark budget profile:

```yaml title="src/plugins/mle_kaggle.yaml (excerpt)"
name: mle_kaggle
description: "Engineering optimization for Kaggle/MLE-bench competitions"
schema_version: 1

eval_contract:
  metric_direction: maximize
  eval_cmd: "bash {cwd}/eval.sh"
  submission_path: "submission.csv"
  sample_submission_path: "data/sample_submission.csv"

protected_paths:
  - "data/**"
  - "private/**"
  - "evaluation/**"

required_outputs:
  - "submission.csv"

profiles:
  mle_bench_lite:                 # 24 h MLE-Bench-Lite budget
    max_cycles: 20
    max_tree_depth: 4
    executor_timeout: 14400       # 4 h per executor
    time_budget: 86400            # 24 h total
```

Select the profile alongside the plugin:

```yaml title="research_config.yaml"
plugin: mle_kaggle
plugin_profile: mle_bench_lite
```

A ready-to-edit config lives at `examples/kaggle_config.example.yaml` in the repository.

## Writing your own plugin

1. Copy `src/plugins/mle_kaggle.yaml` (or the minimal template above) and rename it.
2. Set `name`, `description`, and the `eval_contract` for your domain.
3. Add `protected_paths` / `required_outputs` if your task has data to guard or artifacts
   to produce.
4. Add a `profiles` entry with your compute budget.
5. Tune the agents with the injection points only if you need domain-specific behaviour.

Reference the plugin by its `name` in a config, then launch `arbor`. Pair it with a
[Skill](skills.md) when you want to shape *how* the agent reasons, not just what it
optimizes.
