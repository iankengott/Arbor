{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312;
  pythonEnv = python.withPackages (ps: with ps; [
    anthropic
    openai
    litellm
    tiktoken
    typer
    rich
    pyyaml
    prompt-toolkit
    pydantic
    pydantic-settings
  ]);
in
pkgs.mkShell {
  packages = [
    pythonEnv
    pkgs.git
    pkgs.nodejs_22
  ];

  shellHook = ''
    export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
    echo "Arbor dev shell ready. Try: python -m arbor.cli.app version"
  '';
}
