#!/usr/bin/env python3

import sys
import os
from collections import OrderedDict
home = os.environ['HOME']

required_l = [
'yaml_config_support',
'flowpy'
]
for req in required_l:
    path = '%s/dev_flow/%s' %(home, req)
    sys.path.append(path)
print(sys.path)

#from yaml_config_support.baseValuesFill import BaseValuesFill
from yaml_config_support.cli_config_fill import main
from env import project_subpath, template_dir, valuestore_dir, outpath

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

subpath_string = project_subpath

options = {
    'subpath_string' : subpath_string,
    'default_template_dir': template_dir,
    'default_valuestore_dir': valuestore_dir,
    'outpath': outpath,
    'data_files': data_files,
}


if __name__ == "__main__":
    main(options, argv=[subpath_string])

