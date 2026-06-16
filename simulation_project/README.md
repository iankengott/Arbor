# Arbor Simulation Project Scaffold

This directory is the target project that Arbor should iterate on.
Arbor itself lives one directory up.

For the repo-level AI handoff, onboarding changes, and magnonics/lab-roadmap,
read `../AI_README.md` first. This file remains the Nix/simulation-environment
handoff for `simulation_project/`.

Real storage location:

```text
/mnt/storage/codex-large-projects/Arbor
```

Compatibility symlink:

```text
/home/iank/Desktop/Arbor -> /mnt/storage/codex-large-projects/Arbor
```

Use either path, but prefer the real `/mnt/storage/...` path in new notes so
future worktrees, logs, and outputs clearly live on the second internal drive.

## Mental Model

There are three layers:

```text
1. Arbor agent repository
   /mnt/storage/codex-large-projects/Arbor

2. Simulation target project
   /mnt/storage/codex-large-projects/Arbor/simulation_project

3. External LLM provider
   OpenAI, Anthropic, or another LiteLLM-compatible API
```

Arbor is the outer research agent. It plans experiments, edits this target
project, runs evaluation commands, reads metrics, and decides what to try next.

The LLM is only the reasoning/code-editing brain Arbor talks to through an API.
The LLM does not contain the scientific packages. The scientific runtime is
defined by this project's Nix flake.

The flake answers: when Arbor evaluates an experiment, which Python packages,
simulators, visualization tools, and workflow helpers are available?

The intended loop is:

```text
Arbor starts outside this target project
  -> Arbor creates an experiment branch/worktree
  -> Arbor edits files in this project
  -> Arbor runs the configured evaluation command
  -> the evaluation command enters one Nix flake shell
  -> a script or workflow runs the simulation
  -> the workflow writes outputs/metrics.json
  -> Arbor reads the score/evidence
  -> Arbor keeps, rejects, or refines the idea
```

The key contract is `outputs/metrics.json`. Every experiment should produce
that machine-readable result.

Current placeholder evaluation command:

```bash
nix develop .#base --command python scripts/evaluate.py --config configs/example.yaml
```

## Current Status

Completed so far:

- Cloned and inspected Arbor.
- Added `/mnt/storage/codex-large-projects/Arbor/shell.nix` for Arbor's Python CLI
  dependencies on NixOS.
- Read the simulation tool spreadsheet and wrote the compatibility report at
  `/mnt/storage/codex-large-projects/Arbor/NIXOS_TOOL_COMPATIBILITY.md`.
- Created this standalone target project under `simulation_project/`.
- Added a flake with staged shells instead of one giant all-tools environment.
- Added a placeholder evaluator that writes `outputs/metrics.json`.
- Added `arbor_config.example.yaml` showing Arbor how to call this project.
- Documented the future Docker path below.
- Built and smoke-tested the safe shells one at a time.
- Added `scripts/smoke_shells.sh` to verify start-ready tools before Arbor runs.

This is enough to start wiring Arbor to a reproducible evaluation command. It is
not yet the final scientific workflow.

## Shells

Use the smallest shell that can do the job:

| Shell | Purpose | Status | Realized closure |
| --- | --- | --- | --- |
| `base` | Placeholder evaluator and normal Python data work | Built and smoke-tested | `1.4 GiB` |
| `materials` | Lightweight materials scripting with ASE | Built and smoke-tested | `1.5 GiB` |
| `notebook` | JupyterLab, notebooks, Papermill | Built and smoke-tested | `1.7 GiB` |
| `spin` | Vampire, Spirit, and light materials Python | Built and smoke-tested | `1.6 GiB` |
| `viz` | OVITO and ParaView GUI/CLI tools only | Built and smoke-tested | `4.2 GiB` |
| `atomistic` | Quantum ESPRESSO, LAMMPS, CP2K, GPAW, ASE | Built and smoke-tested | `3.6 GiB` |
| `optimization-lite` | Optuna-only optimization shell | Built and smoke-tested | `1.5 GiB` |
| `optimization` | Optuna, BoTorch, Ax | Deferred to Docker/GPU/cloud unless Nix has cached Torch/Triton | Not realized |
| `pymatgen-heavy` | Pymatgen isolated from normal materials shell | Attempted; stopped after heavy local compile chain | Not realized |
| `full` | Combined packaged stack | Not built; depends on heavy pieces | Not realized |

Important design decision: `pymatgen` is not in `materials` anymore. In this
nixpkgs pin, `pymatgen` pulls a large VTK/GDAL/PyTorch/Triton-adjacent chain.
Keeping it in the default materials shell made normal setup too slow and risky.
Use `pymatgen-heavy` only when a task specifically needs it.

Important design decision: `viz` is GUI-only. OVITO/ParaView bring Python 3.13
packages into the shell, which can conflict with the Python 3.12 scientific env.
Use `materials` or `atomistic` for Python analysis, then use `viz` separately
for visualization.

Start-ready shell contract:

- `base`, `materials`, `notebook`, `spin`, `atomistic`, and
  `optimization-lite` include Python and the Python packages they are expected
  to use at experiment start.
- `viz` intentionally checks only `ovito` and `paraview`; do not treat it as a
  Python analysis shell.
- New tools should be added to `flake.nix` and `scripts/smoke_shells.sh` before
  they become part of a normal Arbor evaluation path.

## Commands

Run the placeholder evaluator:

```bash
nix develop .#base --command python scripts/evaluate.py --config configs/example.yaml
```

Enter common shells:

```bash
nix develop .#materials
nix develop .#notebook
nix develop .#spin
nix develop .#atomistic
nix develop .#viz
nix develop .#optimization-lite
```

Measure realized closure sizes:

```bash
bash scripts/check_env_sizes.sh base
bash scripts/check_env_sizes.sh materials
bash scripts/check_env_sizes.sh notebook
bash scripts/check_env_sizes.sh spin
bash scripts/check_env_sizes.sh atomistic
bash scripts/check_env_sizes.sh viz
bash scripts/check_env_sizes.sh optimization-lite
```

Verify start-ready shell contents:

```bash
bash scripts/smoke_shells.sh
```

Do not casually run:

```bash
bash scripts/check_env_sizes.sh optimization
bash scripts/check_env_sizes.sh pymatgen-heavy
bash scripts/check_env_sizes.sh full
```

Those are intentionally isolated because they may trigger long local compiles.
If you test them, run one at a time with a timeout and check for orphaned build
processes afterward.

## Smoke Tests Already Run

These passed:

```bash
nix develop .#base --command python scripts/evaluate.py --config configs/example.yaml
nix develop .#materials --command python -c 'import ase, numpy, pandas'
nix develop .#notebook --command python -c 'import notebook, jupyterlab, papermill'
nix develop .#spin --command bash -lc 'command -v vampire; command -v spirit; python -c "import ase"'
nix develop .#atomistic --command bash -lc 'command -v pw.x; command -v lmp; command -v gpaw; python -c "import ase, gpaw"'
nix develop .#viz --command bash -lc 'command -v ovito; command -v paraview'
nix develop .#optimization-lite --command python -c 'import optuna; print(optuna.__version__)'
bash scripts/smoke_shells.sh
```

Known atomistic binary names:

- Quantum ESPRESSO: `pw.x`
- LAMMPS: `lmp`
- CP2K: `cp2k.psmp`
- GPAW: `gpaw`

## Tool Compatibility Result

The spreadsheet listed 52 tools. The local nixpkgs compatibility check found 17
available or partially available under common package names.

That is enough to begin because the available set includes:

- materials scripting: `ASE`
- atomistic/DFT/MD: `Quantum ESPRESSO`, `GPAW`, `CP2K`, `LAMMPS`
- notebooks/reports: `Jupyter`, `Papermill`
- optimization/modeling path: `Optuna`, `BoTorch`, `Ax`, but heavy locally
- spin/visualization: `Vampire`, `Spirit`, `OVITO`, `ParaView`

Missing tools are not all the same kind of problem.

Commercial or license-bound:

- `VASP`
- `COMSOL`
- `Thermo-Calc`
- `WIEN2k`
- `OVITO Pro`

Likely custom derivation, source build, container, or external install later:

- `mumax3`
- `OOMMF`
- `Ubermag`
- `pycalphad`
- `FiPy`
- `MOOSE`
- `OpenFOAM`
- `Matminer`
- `MACE`
- `NequIP`
- `WarpX`
- `PICLas`

GUI/manual/older workflows:

- `SRIM/TRIM`
- `SIMTRA`
- `SpinW`

The low package count is a warning against building a giant all-tools
environment. It is not a blocker for starting the Arbor loop.

## Known Failed Or Deferred Attempts

- Snakemake was removed from the active base shell after an earlier oversized
  build failed on a `python3.12-pulp-3.3.0` test issue.
- FiPy is deferred because the current nixpkgs package is unsupported for the
  active Python versions in this pin.
- `optimization` was attempted for 8 minutes and timed out while building
  Triton/Torch locally. No orphan build processes were left afterward.
- A first `optimization-lite` attempt using the stock nixpkgs `optuna` package
  also started building Torch/Triton through test inputs. The shell now uses an
  `optuna` override with checks disabled, which keeps runtime dependencies
  light while still importing Optuna successfully.
- `pymatgen-heavy` was attempted separately and immediately planned local
  builds for GDAL, VTK, Torch, and Triton. The attempt was stopped and the path
  is Docker-deferred unless a future workflow specifically needs it.
- `full` was not built because it includes heavy/unproven pieces. Build smaller
  shells first.

## Unfinished Parts Plan

Do not force the unfinished tools into one giant shell. Finish them as separate
tracks so the working shells stay usable.

### Optimization

Current state: `optimization` includes `Optuna`, `BoTorch`, and `Ax`. It was
attempted for 8 minutes and timed out while compiling `Triton/Torch` locally.
The start-ready optimization path is `optimization-lite`, which includes Optuna
without the local Torch/Triton compile.

Plan:

1. Use `optimization-lite` for regular Arbor experiments that only need Optuna.
2. Keep `BoTorch` and `Ax` out of the normal path unless their backend strategy
   is decided.
3. Check whether a different pinned nixpkgs revision can fetch cached
   `torch`, `botorch`, and `ax-platform` instead of compiling Triton locally.
4. If Nix still wants a long local Triton build, keep the BoTorch/Ax path in
   Docker, a GPU image, or cloud/GPU infrastructure.
5. Document whichever path passes, then update the shell table above.

The likely end state is:

```text
optimization-lite: Optuna only, small enough for regular Arbor experiments
optimization-heavy: BoTorch/Ax only if Nix can realize it cleanly
optimization-docker: fallback if Torch/Triton stays painful in Nix
```

### Pymatgen

Current state: `pymatgen-heavy` exists as an isolated shell, but it has not been
realized. A bounded local build attempt immediately planned GDAL, VTK, Torch,
and Triton builds, so this path is deferred to Docker or a future cached Nix
revision. `pymatgen` was removed from `materials` because it pulled a large
dependency chain and made ordinary materials scripting too expensive.

Plan:

1. Keep `materials` lightweight with ASE.
2. Do not retry `pymatgen-heavy` locally unless a concrete workflow needs it.
3. Prefer a Docker-backed pymatgen path or a different cached nixpkgs revision.
4. If it later builds cleanly, smoke-test `import pymatgen` and record the
   closure size.
5. Do not put `pymatgen` back into `materials` unless it becomes cheap and
   reliable in the pinned nixpkgs revision.

### Full Shell

Current state: `full` is intentionally not built. It combines pieces that have
not all passed independently.

Plan:

1. Do not build `full` until every component shell has passed by itself.
2. If `optimization` or `pymatgen-heavy` ends up Docker-backed, either remove
   `full` or redefine it as "Nix-packaged tools only."
3. Treat `full` as a convenience shell, not the main Arbor runtime.
4. Keep Arbor's default evaluation command pointed at `base` until a real
   workflow needs a larger shell.

## Future Docker Path

Use Nix flakes first for the reproducible open-source stack that nixpkgs can
build or fetch cleanly. Add Docker later for tools where Nix is the wrong
boundary.

Good Docker candidates:

- `pymatgen` if the pinned Nix path keeps pulling GDAL/VTK/Torch/Triton builds
- `BoTorch`/`Ax` if local Nix keeps compiling Torch/Triton
- CUDA/GPU ML stacks such as `MACE`, `NequIP`, or `mumax3`
- old or fragile research code
- binary-only vendor tools
- licensed tools that must live outside the Nix store
- workflows with upstream Docker images already maintained by the tool authors

The intended future structure:

```text
simulation_project/
  flake.nix
  docker/
    README.md
    <tool-name>/
      Dockerfile
      run.sh
  scripts/
    evaluate.py
```

Arbor should still call one stable evaluation command. That command may enter a
Nix shell and then launch a Docker container for a specific tool. Docker should
be an implementation detail behind the evaluation script, not something Arbor
has to reason about for every experiment.

## Next Work

Recommended next steps for the next AI or human:

0. If the task is about Arbor onboarding or the magnonics lab demo, switch to
   the repo root and read `../AI_README.md` before changing this scaffold.

1. Keep `base` as Arbor's default evaluation shell until the real metric exists.
2. Replace `scripts/evaluate.py` with the first real simulation workflow once
   the scientific target is chosen.
3. Use `materials`, `atomistic`, `spin`, `viz`, or `optimization-lite` only when the workflow needs
   them.
4. Add real input data under `data/raw/` or document external data locations.
5. Add missing high-value tools one at a time, with each tool documented in this
   README after it is tested.
6. Before ending any future setup pass, run `bash scripts/smoke_shells.sh`.
7. Before ending any future setup pass, check for leftover build processes:

```bash
ps -eo pid,ppid,stat,comm,args | awk '/nix build|nix develop|check_env_sizes|\/build\/source|cc1plus|g\+\+|triton|gdal|vtk|torch/ && $5 !~ /awk/ {print}'
```

## Handoff Message

If a future AI is told "pick up where we left off", start here:

```text
You are continuing /mnt/storage/codex-large-projects/Arbor/simulation_project.
The old path /home/iank/Desktop/Arbor is a symlink to
/mnt/storage/codex-large-projects/Arbor.

Read README.md first. The repo already has a working staged Nix flake.
Do not rebuild every shell at once. Use one shell at a time.

Already built and smoke-tested:
- base: 1.4 GiB
- materials: 1.5 GiB
- notebook: 1.7 GiB
- spin: 1.6 GiB
- atomistic: 3.6 GiB
- viz: 4.2 GiB
- optimization-lite: 1.5 GiB

Known issue:
- optimization timed out compiling Torch/Triton.
- stock nixpkgs optuna pulls Torch/Triton through test inputs; optimization-lite
  disables optuna checks to stay light.
- pymatgen-heavy was attempted and stopped after it planned GDAL, VTK, Torch,
  and Triton local builds. Prefer Docker or a cached Nix revision for pymatgen.
- full has not been built and should wait until all smaller shells pass.

Immediate next task:
1. Choose the first real scientific target.
2. Replace scripts/evaluate.py with that first real simulation workflow.
3. Add real input data under data/raw/ or document external data locations.
4. Run bash scripts/smoke_shells.sh before handing work back.
5. Check for leftover Nix/compiler processes before finishing.

Do not put pymatgen back into materials.
Do not put Python packages into viz; viz is GUI-only because OVITO/ParaView
bring Python 3.13 paths that conflict with the Python 3.12 scientific env.
```
