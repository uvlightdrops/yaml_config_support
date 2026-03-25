#!/usr/bin/env python3
"""CLI-Einstiegspunkt zum Erzeugen finaler YAML-Values aus Templates."""

import argparse
#from yaml_config_support.K8sValuesFill import K8sValuesFill
from .k8sValuesFill import K8sValuesFill

# Globale Variablen und Umgebungsvariablen - default Werte
"""
subpath_string = 'dev'
import os
home = os.environ['HOME']
basedir = f'{home}/{subpath_string}/eip-konfigurationen/codefy/helmchart'
outpath = f'{home}/{subpath_string}/cf'
options = {
    'default_template_dir': f'{basedir}/codefy_values',
    'default_valuestore_dir': f'{home}/codefy_creds',
    'outpath': outpath,
}
"""

def main(options):
    """Startet die CLI mit einem projektbezogenen Options-Dictionary.

    Das übergebene ``options``-Dictionary liefert Standardpfade und die
    ``data_files``-Beschreibung. Die eigentlichen Laufzeitparameter werden
    anschließend per Kommandozeile geparst.

    Erwartete Schlüssel in ``options``:

    * ``default_template_dir``
    * ``default_valuestore_dir``
    * ``outpath``
    * ``data_files``

    Args:
        options: Projektkonfiguration für Standardpfade und Dateidefinitionen.
    """
    parser = argparse.ArgumentParser(description="Test Config Fill")
    parser.add_argument("env", help="Environment to use (prod, test, dev)")
    parser.add_argument('--template_dir', type=str, default=options['default_template_dir'],
                        help='Path to the template main dir (git) ')
    parser.add_argument('--valuestore_dir', type=str, default=options['default_valuestore_dir'],
                        help='Path to the dir which hold the valuesstores yaml')
    parser.add_argument('--ypath_keys', nargs='*', default=['resources'], help='List of keys for yamlpath files')
    parser.add_argument('--ydict_keys', nargs='*', default=['creds', 'user'], help='List of keys for yamldict files')
    parser.add_argument("-o", "--outdir", help="Directory for output")
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose output: Show each substitution", default=False)
    args = parser.parse_args()

    #print(options)
    out_dir = options['outpath']
    if args.outdir:
        out_dir = args.outdir
    template_dir = args.template_dir
    creds_dir = args.valuestore_dir

    CF = K8sValuesFill(args.env, template_dir, creds_dir, options)
    #CF.options = options
    CF.load_files()
    CF.fill_configs()
    CF.write_output(out_dir, args.env)

#if __name__ == "__main__":
#    main(options)
