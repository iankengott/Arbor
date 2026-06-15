#!/usr/bin/env bash
set -euo pipefail

system="$(nix eval --raw --impure --expr 'builtins.currentSystem')"

if [ "$#" -gt 0 ]; then
  shells=("$@")
else
  shells=(base)
fi

for shell in "${shells[@]}"; do
  attr=".#devShells.${system}.${shell}"
  echo "## ${shell}"
  out="$(nix build --no-link --print-out-paths "${attr}")"
  nix path-info --closure-size --human-readable "${out}"
  echo
done
