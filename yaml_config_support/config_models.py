"""Strukturierte Konfigurationsmodelle für den YAML-Fill-Workflow."""

from collections import OrderedDict
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from .exceptions import DataFileConfigurationError, InvalidOptionsError

_VALID_SOURCES = {"private", "project"}
_VALID_TRANSFORMS = {"fill_config_template", "fill_simple_template"}
_VALID_ENV_MODES = {"yes", "no", "together"}


class DataFileSpec(object):
    """Beschreibt eine einzelne Overlay-Datei aus `data_files`."""

    def __init__(self, name, source, transform, env):
        self.name = name
        self.source = source
        self.transform = transform
        self.env = env

    @classmethod
    def from_mapping(cls, name, raw_spec):
        """Erzeugt und validiert eine Dateispezifikation aus einem Mapping.

        Args:
            name: Logischer Name der Datei, z. B. ``creds``.
            raw_spec: Mapping mit den Schlüsseln ``source``, ``transform`` und
                ``env``.

        Returns:
            Eine validierte Instanz von :class:`DataFileSpec`.

        Raises:
            DataFileConfigurationError: Wenn Pflichtfelder fehlen oder ungültige
                Werte enthalten.
        """
        required_keys = {"source", "transform", "env"}
        missing = sorted(required_keys.difference(raw_spec.keys()))
        if missing:
            raise DataFileConfigurationError(
                "data_files[{!r}] fehlt: {}".format(name, ', '.join(missing))
            )

        spec = cls(
            name=name,
            source=str(raw_spec["source"]),
            transform=str(raw_spec["transform"]),
            env=str(raw_spec["env"]),
        )
        spec.validate()
        return spec

    def validate(self):
        """Validiert die fachlichen Werte der Spezifikation."""
        if self.source not in _VALID_SOURCES:
            raise DataFileConfigurationError(
                "Ungültige source für {!r}: {!r}".format(self.name, self.source)
            )
        if self.transform not in _VALID_TRANSFORMS:
            raise DataFileConfigurationError(
                "Ungültige transform für {!r}: {!r}".format(self.name, self.transform)
            )
        if self.env not in _VALID_ENV_MODES:
            raise DataFileConfigurationError(
                "Ungültiger env-Modus für {!r}: {!r}".format(self.name, self.env)
            )

    def file_name(self, environment):
        """Berechnet den Dateinamen passend zur Umgebungsstrategie.

        Args:
            environment: Zielumgebung wie ``dev`` oder ``prod``.

        Returns:
            Der erwartete Dateiname, z. B. ``values_creds_dev.yaml``.
        """
        suffix = "_{}".format(environment) if self.env == "yes" else ""
        return "values_{}{}.yaml".format(self.name, suffix)


class FillOptions(object):
    """Normalisierte Paketoptionen für Defaults und Overlay-Definitionen."""

    def __init__(self, default_template_dir, default_valuestore_dir, outpath, data_files, subpath_string=None, verbose=False):
        self.default_template_dir = default_template_dir
        self.default_valuestore_dir = default_valuestore_dir
        self.outpath = outpath
        self.data_files = data_files
        self.subpath_string = subpath_string
        self.verbose = verbose

    @classmethod
    def from_mapping(cls, options):
        """Normalisiert ein loses Options-Mapping in eine stabile Struktur.

        Args:
            options: Rohes Mapping, wie es aus einem Wrapper-Skript kommt.

        Returns:
            Eine validierte Instanz von :class:`FillOptions`.

        Raises:
            InvalidOptionsError: Wenn Pflichtschlüssel fehlen.
            DataFileConfigurationError: Wenn `data_files` ungültig ist.
        """
        required = {
            "default_template_dir",
            "default_valuestore_dir",
            "outpath",
            "data_files",
        }
        missing = sorted(required.difference(options.keys()))
        if missing:
            raise InvalidOptionsError(
                "Options-Mapping fehlt: {}".format(', '.join(missing))
            )

        raw_data_files = options["data_files"]
        if not isinstance(raw_data_files, Mapping):
            raise InvalidOptionsError("options['data_files'] muss ein Mapping sein")

        data_files = OrderedDict(
            (name, DataFileSpec.from_mapping(name, spec))
            for name, spec in raw_data_files.items()
        )
        return cls(
            default_template_dir=Path(options["default_template_dir"]),
            default_valuestore_dir=Path(options["default_valuestore_dir"]),
            outpath=Path(options["outpath"]),
            data_files=data_files,
            subpath_string=options.get("subpath_string"),
            verbose=bool(options.get("verbose", False)),
        )

    def with_verbose(self, verbose):
        """Gibt eine Kopie der Optionen mit geänderter Verbose-Einstellung zurück."""
        return FillOptions(
            default_template_dir=self.default_template_dir,
            default_valuestore_dir=self.default_valuestore_dir,
            outpath=self.outpath,
            data_files=self.data_files,
            subpath_string=self.subpath_string,
            verbose=verbose
        )

    def to_legacy_mapping(self):
        """Wandelt die Optionen in ein klassisches Dict für Altcode zurück."""
        return {
            "default_template_dir": str(self.default_template_dir),
            "default_valuestore_dir": str(self.default_valuestore_dir),
            "outpath": str(self.outpath),
            "subpath_string": self.subpath_string,
            "verbose": self.verbose,
            "data_files": {
                name: {
                    "source": spec.source,
                    "transform": spec.transform,
                    "env": spec.env,
                }
                for name, spec in self.data_files.items()
            },
        }
