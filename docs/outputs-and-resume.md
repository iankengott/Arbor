# Outputs & Resume

Arbor records everything a run produces so you can inspect it, reproduce it, and pick up
where you left off.

## Session artifacts

Each run gets its own session directory, by default under the target project:

```text
<project>/.arbor/sessions/<run_name>/
```

`<run_name>` defaults to a timestamp; set it explicitly with `--run-name`, or relocate the
whole directory with `--workspace-dir`.

Inside you'll find the run's checkpoint (Idea Tree + message history), logs, and the
final report.

## `REPORT.md`

When a run finishes, Arbor writes a `REPORT.md` — the human-readable write-up of the
study: what was tried, what worked, the evidence behind each conclusion, and the final
result. Use `arbor report` to work with it, and the `/report` slash command during a run
to print artifact paths.

By default Arbor then opens a **read-only Q&A prompt** so you can interrogate the finished
run (disable with `--no-followup`).

## Experiment branches

Every experiment ran on its own git branch in an isolated worktree. Merged improvements
are on trunk; explored-but-unmerged ideas remain as branch refs you can inspect. During a
run, `/branches` lists the explored branch refs and `/tree` prints the Idea Tree snapshot.

## Resuming an interrupted run

If a run is interrupted — you stopped it, the machine rebooted, a budget tripped — resume
from its checkpoint instead of starting over:

```bash
arbor --resume --run-name my-study
```

`--resume` reloads the Idea Tree and message history from the existing session and
continues in the same workspace. Combine it with `--run-name` (or `--workspace-dir`) to
point at the session you want to continue.

!!! tip
    Because the Idea Tree is the durable shared state, resuming restores not just *where*
    the run stopped but *what it had learned* — merged improvements, pruned branches, and
    backpropagated insight are all intact.

## Monitoring while running

- **Terminal dashboard** — live cycle status, Idea Tree, and cost.
- **Read-only web monitor** — auto-starts near port `8765` (`--webui-port` to change,
  `--no-webui` to disable).
- **`/cost`** — print token usage at any time.
