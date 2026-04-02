#!/usr/bin/env python3
"""CLI-Einstiegspunkt zum Erzeugen finaler YAML-Values aus Templates."""

import argparse
from pathlib import Path

from .config_models import FillOptions
from .k8sValuesFill import K8sValuesFill


def build_parser(options):
    """Erzeugt den CLI-Parser für den YAML-Fill-Workflow.

    Args:
        options: Normalisierte Standardwerte für Template-, Value-Store- und
            Ausgabe-Pfade.

    Returns:
        Ein vollständig konfigurierter :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        description="Build a filled YAML config from templates and discrete value stores."
    )
    parser.add_argument("env", help="Environment to use (prod, test, dev)")
    parser.add_argument(
        "--template_dir",
        type=Path,
        default=options.default_template_dir,
        help="Path to the template main dir (git)",
    )
    parser.add_argument(
        "--valuestore_dir",
        type=Path,
        default=options.default_valuestore_dir,
        help="Path to the dir which holds the values store YAML files",
    )
    parser.add_argument("-o", "--outdir", type=Path, help="Directory for output")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Verbose output: show each substitution",
    )
    return parser


def main(options, argv=None):
    """Startet die CLI mit einem projektbezogenen Options-Dictionary.

    Das übergebene ``options``-Objekt liefert Standardpfade und die
    ``data_files``-Beschreibung. Die eigentlichen Laufzeitparameter werden
    anschließend per Kommandozeile geparst.

    Args:
        options: Projektkonfiguration als Mapping oder :class:`FillOptions`.
        argv: Optionale Argumentliste für Tests oder Programmnutzung.

    Returns:
        Pfad zur erzeugten Ausgabedatei.
    """
    normalized_options = options if isinstance(options, FillOptions) else FillOptions.from_mapping(options)
    parser = build_parser(normalized_options)
    args = parser.parse_args(argv)

    runtime_options = normalized_options.with_verbose(args.verbose)
    out_dir = args.outdir or runtime_options.outpath

    fill = K8sValuesFill(
        env=args.env,
        template_dir=args.template_dir,
        creds_dir=args.valuestore_dir,
        options=runtime_options,
    )
    return fill.run(out_dir)
