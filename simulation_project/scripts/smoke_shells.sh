#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 0 ]; then
  shells=("$@")
else
  shells=(base materials notebook spin atomistic optimization-lite viz)
fi

for shell in "${shells[@]}"; do
  echo "## ${shell}"
  case "${shell}" in
    base)
      nix develop ".#${shell}" --command python -c 'import json, yaml, numpy, scipy, pandas, matplotlib, rich, typer; print("python base ok")'
      ;;
    materials)
      nix develop ".#${shell}" --command python -c 'import ase, numpy, scipy, pandas, matplotlib, yaml, rich, typer; print("python materials ok")'
      ;;
    notebook)
      nix develop ".#${shell}" --command python -c 'import notebook, jupyterlab, papermill, numpy, scipy, pandas, matplotlib, yaml, rich, typer; print("python notebook ok")'
      ;;
    spin)
      nix develop ".#${shell}" --command bash -lc 'command -v vampire; command -v spirit; python -c "import ase, numpy, pandas; print(\"python spin ok\")"'
      ;;
    atomistic)
      nix develop ".#${shell}" --command bash -lc 'command -v pw.x; command -v lmp; command -v cp2k.psmp; command -v gpaw; python -c "import ase, gpaw, numpy, pandas; print(\"python atomistic ok\")"'
      ;;
    optimization-lite)
      nix develop ".#${shell}" --command python -c 'import optuna, numpy, scipy, pandas, matplotlib, yaml, rich, typer; print("python optimization-lite ok")'
      ;;
    viz)
      nix develop ".#${shell}" --command bash -lc 'command -v ovito; command -v paraview; echo "viz tools ok"'
      ;;
    *)
      echo "No smoke test is defined for shell: ${shell}" >&2
      exit 2
      ;;
  esac
  echo
done
