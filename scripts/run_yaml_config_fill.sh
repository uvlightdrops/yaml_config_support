#!/bin/bash
# Shell-Skript zum Aufruf des YAML-Config-Fillers mit optionalem Flag zum Behalten temporärer Dateien

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON=python3.6

KEEP_TEMP=0
ARGS=()

for arg in "$@"; do
  if [[ "$arg" == "--keep-temp" ]]; then
    KEEP_TEMP=1
  else
    ARGS+=("$arg")
  fi
done

if [[ $KEEP_TEMP -eq 1 ]]; then
  export YAML_CONFIG_SUPPORT_KEEP_TEMP=1
fi

$PYTHON "$SCRIPT_DIR/cli_yaml_config_fill.py" "${ARGS[@]}"

