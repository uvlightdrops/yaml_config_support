#!/usr/bin/env python3

import sys
import os
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

data_files = {
	'creds': {
		'source': 'private',
		'transform': 'fill_config_template',
		'env': 'yes',
	},
	'resources': {
		'source': 'project',
		'transform': 'fill_simple_template',
		'env': 'together',
	},
	'user': {
		'source': 'private',
		'transform': 'fill_config_template',
		'env': 'no',
	},
}


project_files = ['resources']
private_files = ['creds', 'user']

subpath_string = 'dev'
subpath_string = 'dev_ldbv'
#basedir = f'{home}/{subpath_string}/eip-konfigurationen/codefy/helmchart'
basedir = f'{home}/{subpath_string}'
template_dir    = f'{basedir}/codefy_data/helmchart'
valuestore_dir  = f'{basedir}/codefy_creds' 
outpath = f'{basedir}/cf'

options = {
    'subpath_string' : subpath_string,
    'default_template_dir': template_dir,
    'default_valuestore_dir': valuestore_dir,
    'outpath': outpath,
	'data_files': data_files,
}


if __name__ == "__main__":
    main(**options)

