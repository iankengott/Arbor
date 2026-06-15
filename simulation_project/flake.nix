{
  description = "Staged simulation environment for Arbor-driven materials and magnonics workflows";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs supportedSystems (system:
          f (import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          }));
    in
    {
      devShells = forAllSystems (pkgs:
        let
          py = pkgs.python312;
          basePython = py.withPackages (ps: with ps; [
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          materialsPython = py.withPackages (ps: with ps; [
            ase
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          pymatgenPython = py.withPackages (ps: with ps; [
            pymatgen
            ase
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          notebookPython = py.withPackages (ps: with ps; [
            jupyterlab
            notebook
            papermill
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          optunaLite = pkgs.python312Packages.optuna.overridePythonAttrs (old: {
            doCheck = false;
            nativeCheckInputs = [ ];
          });

          optimizationLitePython = py.withPackages (ps: with ps; [
            optunaLite
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          optimizationPython = py.withPackages (ps: with ps; [
            optuna
            botorch
            ax-platform
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          dftPython = py.withPackages (ps: with ps; [
            ase
            gpaw
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
          ]);

          fullPython = py.withPackages (ps: with ps; [
            ase
            gpaw
            optuna
            botorch
            ax-platform
            jupyterlab
            notebook
            papermill
            numpy
            scipy
            pandas
            matplotlib
            pyyaml
            rich
            typer
          ]);

          commonShellHook = ''
            export SIM_PROJECT_ROOT="$PWD"
            mkdir -p data/raw data/processed outputs logs
            echo "Simulation project shell ready: $SIM_PROJECT_ROOT"
          '';
        in
        {
          base = pkgs.mkShell {
            name = "simulation-base";
            packages = [
              basePython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };

          materials = pkgs.mkShell {
            name = "simulation-materials";
            packages = [
              materialsPython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };

          pymatgen-heavy = pkgs.mkShell {
            name = "simulation-pymatgen-heavy";
            packages = [
              pymatgenPython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };

          notebook = pkgs.mkShell {
            name = "simulation-notebook";
            packages = [
              notebookPython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };

          optimization = pkgs.mkShell {
            name = "simulation-optimization";
            packages = [
              optimizationPython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };

          optimization-lite = pkgs.mkShell {
            name = "simulation-optimization-lite";
            packages = [
              optimizationLitePython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };

          atomistic = pkgs.mkShell {
            name = "simulation-atomistic";
            packages = [
              dftPython
              pkgs.git
              pkgs.quantum-espresso
              pkgs.lammps
              pkgs.cp2k
            ];
            shellHook = commonShellHook;
          };

          spin = pkgs.mkShell {
            name = "simulation-spin";
            packages = [
              materialsPython
              pkgs.git
              pkgs.vampire
              pkgs.spirit
            ];
            shellHook = commonShellHook;
          };

          viz = pkgs.mkShell {
            name = "simulation-viz";
            packages = [
              pkgs.git
              pkgs.ovito
              pkgs.paraview
            ];
            shellHook = commonShellHook;
          };

          full = pkgs.mkShell {
            name = "simulation-full-packaged";
            packages = [
              fullPython
              pkgs.git
              pkgs.quantum-espresso
              pkgs.lammps
              pkgs.cp2k
              pkgs.ovito
              pkgs.paraview
              pkgs.vampire
              pkgs.spirit
            ];
            shellHook = commonShellHook;
          };

          default = pkgs.mkShell {
            name = "simulation-base";
            packages = [
              basePython
              pkgs.git
            ];
            shellHook = commonShellHook;
          };
        });
    };
}
