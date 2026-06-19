#!/usr/bin/env python3

import argparse
import sys
import os
from pathlib import Path

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

#from yaml_config_support.baseValuesFill import BaseValuesFill
from yaml_config_support.cli_config_fill import main
from env import (
    basedir,
    data_file_defaults,
    data_files,
    outpath,
    target_env,
    template_defaults,
    template_dir,
    template_files,
    valuestore_dir,
)

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Fill overlay manifests and write generated files to configured outpath."
    )
    parser.add_argument(
        "env",
        nargs="?",
        default=target_env,
        help="Environment suffix for value lookup/output naming (default from env.py)",
    )
    parser.add_argument(
        "--overlay",
        default=None,
        help="Overlay directory name under k8s/overlays (default: value of env argument)",
    )
    return parser.parse_args(argv)


def build_options(overlay_name: str):
    dynamic_template_dir = Path(template_dir) / "overlays" / overlay_name
    if not dynamic_template_dir.exists():
        raise SystemExit(f"Overlay-Verzeichnis nicht gefunden: {dynamic_template_dir}")
    return {
        "subpath_string": str(basedir),
        "default_template_dir": dynamic_template_dir,
        "default_valuestore_dir": valuestore_dir,
        "outpath": outpath,
        "template_defaults": template_defaults,
        "template_files": template_files,
        "data_file_defaults": data_file_defaults,
        "data_files": data_files,
    }


if __name__ == "__main__":
    cli_args = parse_args()
    overlay_name = cli_args.overlay or cli_args.env
    options = build_options(overlay_name)
    main(options, argv=[cli_args.env])

