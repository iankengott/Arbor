# NixOS Compatibility Report

Source workbook: `/home/iank/Downloads/updated_simulation_tool_stack.xlsx`.

Checked against the current local nixpkgs available to this machine using direct attribute evaluation. This is a packaging report, not a scientific suitability report.

## Summary

- Available or partial in this nixpkgs scan: 17 / 52
- Not found under common nixpkgs names: 35 / 52
- Licensed/manual/research-code tools may still run on NixOS, but they need a separate installer, source build, container, Wine/Windows VM, or custom derivation.

## Tool Matrix

| Tier | Tool | NixOS status | nixpkgs attributes found | Notes |
| --- | --- | --- | --- | --- |
| Core | ASE | Available | `python313Packages.ase`, `python312Packages.ase` |  |
| Core | pymatgen | Available | `python313Packages.pymatgen`, `python312Packages.pymatgen` |  |
| Core | Materials Project API | Partial | `python313Packages.pymatgen` | mp-api was not found by attribute scan; pymatgen is available and can cover some Materials Project workflows depending on version/API usage. |
| Core | Atomsk | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | OpenKIM | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | Quantum ESPRESSO | Available | `quantum-espresso` |  |
| Core | GPAW | Available | `python313Packages.gpaw`, `python312Packages.gpaw` |  |
| Core | LAMMPS | Available | `lammps`, `lammps-mpi` |  |
| Core | OVITO / OVITO Python | Available | `ovito` |  |
| Core | SRIM / TRIM | Not found |  | Windows/manual freeware workflow; not a native nixpkgs package here. |
| Core | SIMTRA | Not found |  | Research software; not packaged in this nixpkgs channel. |
| Core | Python SIMTRA wrapper / multicathode workflow | Not found |  | Likely custom research wrapper; package/repo must be supplied separately. |
| Core | pycalphad | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | mumax3 | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | OOMMF | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | Ubermag | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | Fidimag | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Core | Snakemake | Available | `snakemake`, `python313Packages.snakemake`, `python312Packages.snakemake` |  |
| Core | Jupyter + Papermill | Partial | `jupyter`, `python313Packages.jupyterlab`, `python313Packages.notebook`, `python313Packages.papermill`, `python312Packages.papermill` | Available through Jupyter/JupyterLab/notebook plus papermill Python packages. |
| Add soon | SDTrimSP | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | F-TRIDYN | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | ESPEI | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | MOOSE | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | FiPy | Partial | `python313Packages.fipy`, `python312Packages.fipy` | Attribute exists, but it did not realize in the pinned flake because this nixpkgs marks FiPy unsupported for Python 3.12/3.13. Integrate later with a compatible interpreter or custom package set. |
| Add soon | OpenFOAM | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | Vampire | Available | `vampire` |  |
| Add soon | UppASD | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | Spirit | Available | `spirit` |  |
| Add soon | Matminer | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Add soon | Optuna | Available | `python313Packages.optuna`, `python312Packages.optuna` |  |
| Add soon | BoTorch / Ax | Partial | `python313Packages.botorch`, `python313Packages.ax-platform`, `python312Packages.botorch`, `python312Packages.ax-platform` | Both BoTorch and Ax are available as Python packages. |
| Optional licensed | VASP | Not found |  | Licensed commercial/academic code; not in public nixpkgs. |
| Optional licensed | Thermo-Calc + TC-Python | Not found |  | Commercial licensed software; keep outside open base env. |
| Optional licensed | COMSOL Multiphysics | Not found |  | Commercial licensed software; keep outside open base env. |
| Optional licensed | OVITO Pro | Partial | `ovito` | Partial: open OVITO package exists, Pro license/features are separate. |
| Manual / reference | SpinW | Not found |  | MATLAB/Octave-oriented workflow; not packaged here. |
| Manual / reference | WIEN2k | Not found |  | Commercial academic package; not in public nixpkgs here. |
| Manual / reference | OpenCalphad | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | CP2K | Available | `cp2k` |  |
| Advanced / research | ABINIT | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | GPUMD | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | PRISMS-PF | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | WarpX | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | picFoam / OpenFOAM plasma workflows | Not found |  | OpenFOAM itself was not visible in this channel under common names; picFoam workflow likely custom. |
| Advanced / research | PICLas | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | MACE | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | NequIP / Allegro | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Advanced / research | Magpylib | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Support | ParaView | Available | `paraview` |  |
| Support | atomate2 + jobflow | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Support | FireWorks | Not found |  | Not found under common package names in this local nixpkgs scan. |
| Support | AFLOW / AFLOW++ | Not found |  | Not visible in this channel under common names; may need binary/source/custom derivation. |

## Recommended Staging

Start with `simulation_project/.#base` for Python automation, data handling, workflow execution, and lightweight modeling. Add `.#atomistic`, `.#spin`, or `.#viz` only when a task needs those solvers/viewers. Keep unavailable or licensed packages outside the core shell until you have access details.
