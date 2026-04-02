#!/usr/bin/env python3
"""Projektbezogener Wrapper für :mod:`yaml_config_support.cli_config_fill`.

Das Skript definiert die ``data_files``-Konfiguration und Standardpfade für ein
konkretes Projektsetup und reicht diese gesammelt an ``main(options)`` weiter.
"""

from collections import OrderedDict
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from yaml_config_support.cli_config_fill import main


data_files = OrderedDict(
    [
        (
            "creds",
            {
                "source": "private",
                "transform": "fill_config_template",
                "env": "yes",
            },
        ),
        (
            "resources",
            {
                "source": "project",
                "transform": "fill_simple_template",
                "env": "together",
            },
        ),
        (
            "user",
            {
                "source": "private",
                "transform": "fill_config_template",
                "env": "no",
            },
        ),
    ]
)

from env import *
"""
project_subpath = "dev_ldbv"
home_dir = Path.home()
basedir = home_dir / project_subpath
template_dir = basedir / "codefy_data" / "helmchart"
valuestore_dir = basedir / "codefy_creds"
outpath = basedir / "cf"
"""

options = {
    "subpath_string": project_subpath,
    "default_template_dir": template_dir,
    "default_valuestore_dir": valuestore_dir,
    "outpath": outpath,
    "data_files": data_files,
}


if __name__ == "__main__":
    main(options)
