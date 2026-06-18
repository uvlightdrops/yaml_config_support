"""Strukturierte Konfigurationsmodelle für den YAML-Fill-Workflow."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from .exceptions import DataFileConfigurationError, InvalidOptionsError

_VALID_SOURCES = {"private", "project"}
_VALID_TRANSFORMS = {"fill_config_template", "fill_simple_template"}
_VALID_ENV_MODES = {"yes", "no", "together", "fallback"}


def _merge_defaults(raw_spec: Mapping[str, Any] | None, defaults: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = dict(defaults or {})
    if raw_spec:
        merged.update(raw_spec)
    return merged


@dataclass(frozen=True)
class DataFileSpec:
    """Beschreibt eine einzelne Overlay-Datei aus `data_files`."""

    name: str
    source: str
    transform: str
    env: str

    @classmethod
    def from_mapping(
        cls,
        name: str,
        raw_spec: Mapping[str, Any] | None,
        defaults: Mapping[str, Any] | None = None,
    ) -> "DataFileSpec":
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
        merged_spec = _merge_defaults(raw_spec, defaults)
        required_keys = {"source", "transform", "env"}
        missing = sorted(required_keys.difference(merged_spec.keys()))
        if missing:
            raise DataFileConfigurationError(
                f"data_files[{name!r}] fehlt: {', '.join(missing)}"
            )

        spec = cls(
            name=name,
            source=str(merged_spec["source"]),
            transform=str(merged_spec["transform"]),
            env=str(merged_spec["env"]),
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
        """Berechnet den primären Dateinamen passend zur Umgebungsstrategie.

        Args:
            environment: Zielumgebung wie ``dev`` oder ``prod``.

        Returns:
            Der erwartete Dateiname, z. B. ``values_creds_dev.yaml``.
        """
        suffix = f"_{environment}" if self.env == "yes" else ""
        return f"values_{self.name}{suffix}.yaml"

    def file_names(self, environment: str) -> list:
        """Gibt alle Dateinamen zurück, die für diese Spezifikation in Prioritätsreihenfolge zu prüfen sind.

        Bei ``env == 'fallback'``: zuerst umgebungsspezifisch, dann allgemein.
        Alle anderen Modi liefern genau einen Namen.

        Args:
            environment: Zielumgebung wie ``dev`` oder ``prod``.

        Returns:
            Liste mit einem oder zwei Dateinamen.
        """
        if self.env == "fallback":
            return [
                f"values_{self.name}_{environment}.yaml",  # zuerst: spezifisch
                f"values_{self.name}.yaml",                # Fallback: allgemein
            ]
        return [self.file_name(environment)]


@dataclass(frozen=True)
class TemplateFileSpec:
    """Beschreibt eine Template-Datei, die als Basis oder Overlay geladen wird."""

    path: str
    source: str = "project"
    transform: str = "fill_config_template"

    @classmethod
    def from_raw(
        cls,
        raw_spec: str | Path | Mapping[str, Any],
        defaults: Mapping[str, Any] | None = None,
    ) -> "TemplateFileSpec":
        effective_defaults = {
            "source": "project",
            "transform": "fill_config_template",
        }
        if defaults:
            effective_defaults.update(defaults)

        if isinstance(raw_spec, (str, Path)):
            merged_spec = _merge_defaults({"path": str(raw_spec)}, effective_defaults)
        elif isinstance(raw_spec, Mapping):
            merged_spec = _merge_defaults(raw_spec, effective_defaults)
        else:
            raise InvalidOptionsError("template_files muss Strings/Pfade oder Mappings enthalten")

        required_keys = {"path", "source", "transform"}
        missing = sorted(required_keys.difference(merged_spec.keys()))
        if missing:
            raise InvalidOptionsError(
                f"template_files-Eintrag fehlt: {', '.join(missing)}"
            )

        spec = cls(
            path=str(merged_spec["path"]),
            source=str(merged_spec["source"]),
            transform=str(merged_spec["transform"]),
        )
        if spec.source not in _VALID_SOURCES:
            raise InvalidOptionsError(f"Ungültige source für template_files: {spec.source!r}")
        if spec.transform not in _VALID_TRANSFORMS:
            raise InvalidOptionsError(f"Ungültige transform für template_files: {spec.transform!r}")
        return spec

@dataclass(frozen=True)
class FillOptions:
    """Normalisierte Paketoptionen für Defaults und Overlay-Definitionen."""

    default_template_dir: Path
    default_valuestore_dir: Path
    outpath: Path
    data_files: "OrderedDict[str, DataFileSpec]"
    template_files: tuple[TemplateFileSpec, ...]
    template_file_name: str = "values_onefitsall.yaml"
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

        data_file_defaults = options.get("data_file_defaults", {})
        if data_file_defaults and not isinstance(data_file_defaults, Mapping):
            raise InvalidOptionsError("options['data_file_defaults'] muss ein Mapping sein")

        raw_data_files = options["data_files"]
        if not isinstance(raw_data_files, Mapping):
            raise InvalidOptionsError("options['data_files'] muss ein Mapping sein")

        data_files: "OrderedDict[str, DataFileSpec]" = OrderedDict(
            (name, DataFileSpec.from_mapping(name, spec, data_file_defaults))
            for name, spec in raw_data_files.items()
        )

        template_defaults = options.get("template_defaults", {})
        if template_defaults and not isinstance(template_defaults, Mapping):
            raise InvalidOptionsError("options['template_defaults'] muss ein Mapping sein")

        raw_template_files = options.get("template_files")
        if raw_template_files is None:
            raw_template_files = [options.get("template_file_name", "values_onefitsall.yaml")]
        elif isinstance(raw_template_files, (str, Path)):
            raw_template_files = [raw_template_files]

        template_files = tuple(
            TemplateFileSpec.from_raw(raw_spec, template_defaults)
            for raw_spec in raw_template_files
        )
        if not template_files:
            raise InvalidOptionsError("options['template_files'] darf nicht leer sein")

        return cls(
            default_template_dir=Path(options["default_template_dir"]),
            default_valuestore_dir=Path(options["default_valuestore_dir"]),
            outpath=Path(options["outpath"]),
            data_files=data_files,
            template_files=template_files,
            template_file_name=template_files[0].path,
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
            "template_files": [
                {
                    "path": spec.path,
                    "source": spec.source,
                    "transform": spec.transform,
                }
                for spec in self.template_files
            ],
            "template_file_name": self.template_file_name,
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

