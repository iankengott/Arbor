# Preparing a Benchmark

You don't write a config to point Arbor at a task. You prepare **two things** and let the
interactive CLI do the rest:

1. A **baseline repo** — your code and data, plus a way to score a result.
2. A plain-language **README** describing the task, the metric, and the goal.

Then you run `arbor` inside the repo. The intake agent reads your README and eval script,
confirms the metric and current baseline with you, proposes a plan, and launches the
study. No hand-written YAML, no eval contract to author.

## 1. A baseline repo

Put everything in one directory — typically the repo you already have:

```text
my_task/
├── data/            # datasets and any fixed inputs
├── eval.sh          # scores a candidate and prints the metric
├── train.py         # your starting-point code (Arbor edits this)
└── README.md        # plain-language description of the task
```

The only hard requirement is that Arbor can **run something to get a score**. Your
`eval.sh` (or `python eval.py`, `make eval`, …) should print the metric on a line Arbor
can read, for example:

```text
score: 0.8123
```

A simple working baseline already in the repo is ideal — it gives Arbor a number to beat
and confirms the eval actually runs.

!!! tip "Let the intake agent do the plumbing"
    You don't have to pre-initialize git, `chmod +x` your script, or run the eval yourself.
    When you launch `arbor`, the intake agent will quietly do those setup steps for you
    (and confirm the eval produces a score) before the study starts.

## 2. A plain-language README

This is where you describe the task — in normal prose, the way you'd brief a colleague.
Cover four things:

- **The task** — what the project is and what a solution looks like.
- **The metric** — which number is being optimized and whether higher or lower is better
  (e.g. "maximize accuracy printed by `bash eval.sh`").
- **The goal** — how ambitious this run is ("beat the baseline", "get above 60%", or
  "push as high as possible").
- **What's off-limits** — anything Arbor must not modify, such as `data/` or the eval
  script itself.

You don't need a special format or fields — Arbor reads the README the way a person would.
The clearer your description, the better the agent's first plan.

## 3. Launch and confirm

From inside the repo, start the interactive CLI:

```bash
cd my_task
arbor
```

In the **intake chat**, the agent reads your README and eval script, states the metric,
baseline, goal, and constraints it inferred, and asks you to confirm or correct them in one
shot. Say "go" and it launches the study — proposing hypotheses, editing your code, running
real experiments, and keeping only the changes that improve the held-out score.

That's the whole setup. Everything Arbor needs — how to evaluate, what to protect, what
counts as "better" — comes from your repo and the short confirmation, not from a config
file you maintain.

!!! note "Held-out discipline"
    Arbor iterates on a **dev** signal but only keeps a change if it improves a **held-out**
    metric by a margin. That is what prevents overfitting to the iteration signal. See
    [How It Works → Evaluation discipline](how-it-works.md#evaluation-discipline).

## Going further

For a **one-off** study, the steps above are all you need. If you run the **same kind of
benchmark repeatedly** — and want to pin the exact eval contract, protected paths, budget,
and domain guidance so every run is identical — capture them once in a
[plugin](plugins.md). Arbor ships one for Kaggle / MLE-bench (`mle_kaggle`) as a worked
example.
