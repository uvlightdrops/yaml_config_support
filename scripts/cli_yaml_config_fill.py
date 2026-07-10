#!/usr/bin/env python3

import argparse
import sys
import os
from pathlib import Path
from importlib import import_module

import yaml

MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:
    raise SystemExit(
        "Python >= "
        f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]} erforderlich, "
        f"gefunden: {sys.version_info.major}.{sys.version_info.minor}. "
        "Nutze z. B. PYTHON_BIN=python3.11 cli_yaml_config_fill ..."
    )

home = os.environ['HOME']

required_l = [
'yaml_config_support',
'flowpy'
]
for req in required_l:
    path = '%s/dev_flow/%s' %(home, req)
    sys.path.append(path)

# env.py zuerst im aktuellen Arbeitsverzeichnis suchen (Aufrufer-Verzeichnis),
# dann im Verzeichnis dieses Skripts als Fallback
_caller_dir = str(Path.cwd())
_script_dir = str(Path(__file__).resolve().parent)
if _caller_dir not in sys.path:
    sys.path.insert(0, _caller_dir)
if _script_dir not in sys.path:
    sys.path.insert(1, _script_dir)

from yaml_config_support.env_validator import validate_env_config
from yaml_config_support.cli_config_fill import main


def _load_yaml_env_config(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"YAML-Fehler in {path}: {e}")
    if not isinstance(payload, dict):
        raise SystemExit(f"Ungueltige YAML-Konfiguration in {path}: Mapping erwartet")
    validate_env_config(payload, path)
    return payload


def _to_path(value):
    return Path(value) if value is not None else None


def _normalize_config(raw: dict, source: Path | str) -> dict:
    required = ["basedir", "template_dir", "valuestore_dir", "outpath", "data_files"]
    missing = [key for key in required if key not in raw]
    if missing:
        raise SystemExit(f"Konfiguration {source} unvollstaendig, fehlt: {', '.join(missing)}")

    return {
        "basedir": _to_path(raw["basedir"]),
        "template_dir": _to_path(raw["template_dir"]),
        "template_collect_dir": _to_path(raw.get("template_collect_dir")),
        "valuestore_dir": _to_path(raw["valuestore_dir"]),
        "outpath": _to_path(raw["outpath"]),
        "target_env": raw.get("target_env", "dev"),
        "template_defaults": raw.get(
            "template_defaults", {"source": "project", "transform": "fill_config_template"}
        ),
        "template_files": raw.get("template_files", []),
        "data_file_defaults": raw.get("data_file_defaults", {}),
        "data_files": raw["data_files"],
    }


def load_project_config() -> dict:
    # Prioritaet: env.yaml/env.yml im Aufruferverzeichnis, dann env.py
    yaml_candidates = [
        Path.cwd() / "env.yaml",
        Path.cwd() / "env.yml",
        Path(_script_dir) / "env.yaml",
        Path(_script_dir) / "env.yml",
    ]
    for candidate in yaml_candidates:
        if candidate.exists():
            return _normalize_config(_load_yaml_env_config(candidate), candidate)

    env_module = import_module("env")
    raw = {
        "basedir": getattr(env_module, "basedir"),
        "template_dir": getattr(env_module, "template_dir"),
        "template_collect_dir": getattr(env_module, "template_collect_dir", None),
        "valuestore_dir": getattr(env_module, "valuestore_dir"),
        "outpath": getattr(env_module, "outpath"),
        "target_env": getattr(env_module, "target_env", "dev"),
        "template_defaults": getattr(env_module, "template_defaults", {}),
        "template_files": getattr(env_module, "template_files", []),
        "data_file_defaults": getattr(env_module, "data_file_defaults", {}),
        "data_files": getattr(env_module, "data_files"),
    }
    return _normalize_config(raw, "env.py")

def parse_args(default_env, argv=None):
    parser = argparse.ArgumentParser(
        description="Fill overlay manifests and write generated files to configured outpath."
    )
    parser.add_argument(
        "env",
        nargs="?",
        default=default_env,
        help="Environment suffix for value lookup/output naming (default from env config)",
    )
    parser.add_argument(
        "--overlay",
        default=None,
        help="Overlay directory name under k8s/overlays (default: value of env argument)",
    )
    return parser.parse_args(argv)


def build_options(config: dict, overlay_name: str):
    template_dir = config["template_dir"]
    explicit_collect_dir = config["template_collect_dir"]
    overlay_dir = explicit_collect_dir or (template_dir / "overlays" / overlay_name)
    if not overlay_dir.exists():
        raise SystemExit(f"Overlay-Verzeichnis nicht gefunden: {overlay_dir}")

    # Wichtig: project-data_files (z.B. values_resources.yaml) werden relativ zum
    # Template-Root gesucht, nicht im Overlay-Verzeichnis.
    return {
        "subpath_string": str(config["basedir"]),
        "default_template_dir": Path(template_dir),
        "default_valuestore_dir": config["valuestore_dir"],
        "outpath": config["outpath"],
        "template_defaults": config["template_defaults"],
        "template_collect_dir": str(overlay_dir),
        "template_files": config["template_files"],
        "data_file_defaults": config["data_file_defaults"],
        "data_files": config["data_files"],
    }


if __name__ == "__main__":
    config = load_project_config()
    cli_args = parse_args(config["target_env"])
    overlay_name = cli_args.overlay or cli_args.env
    options = build_options(config, overlay_name)
    main(options, argv=[cli_args.env])
