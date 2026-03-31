"""Strukturierte Konfigurationsmodelle für den YAML-Fill-Workflow."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from .exceptions import DataFileConfigurationError, InvalidOptionsError

_VALID_SOURCES = {"private", "project"}
_VALID_TRANSFORMS = {"fill_config_template", "fill_simple_template"}
_VALID_ENV_MODES = {"yes", "no", "together"}


@dataclass(frozen=True)
class DataFileSpec:
    """Beschreibt eine einzelne Overlay-Datei aus `data_files`."""

    name: str
    source: str
    transform: str
    env: str

    @classmethod
    def from_mapping(cls, name: str, raw_spec: Mapping[str, Any]) -> "DataFileSpec":
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
                f"data_files[{name!r}] fehlt: {', '.join(missing)}"
            )

        spec = cls(
            name=name,
            source=str(raw_spec["source"]),
            transform=str(raw_spec["transform"]),
            env=str(raw_spec["env"]),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        """Validiert die fachlichen Werte der Spezifikation."""
        if self.source not in _VALID_SOURCES:
            raise DataFileConfigurationError(
                f"Ungültige source für {self.name!r}: {self.source!r}"
            )
        if self.transform not in _VALID_TRANSFORMS:
            raise DataFileConfigurationError(
                f"Ungültige transform für {self.name!r}: {self.transform!r}"
            )
        if self.env not in _VALID_ENV_MODES:
            raise DataFileConfigurationError(
                f"Ungültiger env-Modus für {self.name!r}: {self.env!r}"
            )

    def file_name(self, environment: str) -> str:
        """Berechnet den Dateinamen passend zur Umgebungsstrategie.

        Args:
            environment: Zielumgebung wie ``dev`` oder ``prod``.

        Returns:
            Der erwartete Dateiname, z. B. ``values_creds_dev.yaml``.
        """
        suffix = f"_{environment}" if self.env == "yes" else ""
        return f"values_{self.name}{suffix}.yaml"


@dataclass(frozen=True)
class FillOptions:
    """Normalisierte Paketoptionen für Defaults und Overlay-Definitionen."""

    default_template_dir: Path
    default_valuestore_dir: Path
    outpath: Path
    data_files: "OrderedDict[str, DataFileSpec]"
    subpath_string: str | None = None
    verbose: bool = False

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any]) -> "FillOptions":
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
                f"Options-Mapping fehlt: {', '.join(missing)}"
            )

        raw_data_files = options["data_files"]
        if not isinstance(raw_data_files, Mapping):
            raise InvalidOptionsError("options['data_files'] muss ein Mapping sein")

        data_files: "OrderedDict[str, DataFileSpec]" = OrderedDict(
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

    def with_verbose(self, verbose: bool) -> "FillOptions":
        """Gibt eine Kopie der Optionen mit geänderter Verbose-Einstellung zurück."""
        return replace(self, verbose=verbose)

    def to_legacy_mapping(self) -> MutableMapping[str, Any]:
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

