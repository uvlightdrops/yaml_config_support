#!/usr/bin/env python3
import argparse
import os
import shutil
from yamlTemplateFillSupport import YamlTemplateFillSupport
from yaml_config_support.K8sValuesFill import K8sValuesFill

# Globale Variablen und Umgebungsvariablen
home = os.environ['HOME']
subpath_string = 'dev'
basedir = f'{home}/{subpath_string}/eip-konfigurationen/codefy/helmchart'
default_template_dir = basedir
default_valuestore_dir = f'{home}/codefy_creds'

def main():
    parser = argparse.ArgumentParser(description="Test Config Fill")
    parser.add_argument("env", help="Environment to use (prod, test, dev)")
    parser.add_argument('--template_dir', type=str, default=default_template_dir,
                        help='Path to the template main dir (git) ')
    parser.add_argument('--valuestore_dir', type=str, default=default_valuestore_dir,
                        help='Path to the dir which hold the valuesstores yaml')
    parser.add_argument("-o", "--outdir", help="Directory for output")
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose output: Show each substitution", default=False)
    args = parser.parse_args()
    outpath = f'{home}/{subpath_string}/cf/cf-{args.env}'
    if args.outdir:
        outpath = args.outdir
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    out_fp = f'{outpath}/updated_values-{args.env}.yaml'
    if os.path.exists(out_fp):
        if args.verbose:
            print(f'Target output file existed: {out_fp}, making backup')
        shutil.copy(out_fp, out_fp+'_bak.yaml')
    template_dir = args.template_dir
    creds_dir = args.valuestore_dir
    CF = K8sValuesFill(template_dir, creds_dir, env=args.env, verbose=args.verbose)
    CF.load_files()
    CF.test_config_fill(out_fp)

if __name__ == "__main__":
    main()
