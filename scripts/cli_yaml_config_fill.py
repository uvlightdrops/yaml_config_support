#!/usr/bin/env python3

import sys
import os
from pathlib import Path

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
    data_file_defaults,
    data_files,
    outpath,
    project_subpath,
    target_env,
    template_defaults,
    template_dir,
    template_files,
    valuestore_dir,
)

subpath_string = project_subpath

options = {
    'subpath_string' : subpath_string,
    'default_template_dir': template_dir,
    'default_valuestore_dir': valuestore_dir,
    'outpath': outpath,
    'template_defaults': template_defaults,
    'template_files': template_files,
    'data_file_defaults': data_file_defaults,
    'data_files': data_files,
}


if __name__ == "__main__":
    main(options, argv=[target_env])

