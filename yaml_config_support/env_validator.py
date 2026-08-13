"""Schema-Validierung für env.yaml/env.yml Konfigurationsdateien."""

from typing import Any, Mapping, Sequence
from pathlib import Path


class EnvConfigValidationError(Exception):
    """Fehler bei der Validierung der env-Konfiguration."""
    pass


def validate_env_config(config: dict, source: Path | str) -> None:
    """Validiert eine Projektkonfiguration gegen das erwartete Schema.
    
    Args:
        config: Die geladene Konfiguration (aus env.yaml oder env.py)
        source: Quelle (Dateiname oder Path) für Fehlermeldungen
        
    Raises:
        EnvConfigValidationError: Wenn die Konfiguration ungültig ist
    """
    if not isinstance(config, dict):
        raise EnvConfigValidationError(
            f"{source}: Konfiguration muss ein Mapping sein, nicht {type(config).__name__}"
        )

    required_top_level = {"basedir", "template_dir", "valuestore_dir", "outpath", "data_files"}
    missing = sorted(required_top_level - set(config.keys()))
    if missing:
        raise EnvConfigValidationError(
            f"{source}: Erforderliche Top-Level-Keys fehlen: {', '.join(missing)}"
        )

    # Optionale Top-Level-Keys mit Typprüfung
    optional_top = {
        "target_env": str,
        "template_collect_dir": (str, type(None)),
        "template_files": (list, tuple),
        "template_defaults": dict,
        "data_file_defaults": dict,
    }
    for key, expected_type in optional_top.items():
        if key in config:
            value = config[key]
            if not isinstance(value, expected_type):
                raise EnvConfigValidationError(
                    f"{source}.{key}: Typ muss {expected_type} sein, nicht {type(value).__name__}"
                )

    # data_files Validierung
    data_files = config.get("data_files")
    if not isinstance(data_files, dict):
        raise EnvConfigValidationError(
            f"{source}.data_files: Muss ein Mapping sein, nicht {type(data_files).__name__}"
        )

    if not data_files:
        raise EnvConfigValidationError(f"{source}.data_files: Darf nicht leer sein")

    _VALID_SOURCES = {"private", "project"}
    _VALID_TRANSFORMS = {"fill_config_template", "fill_simple_template"}
    _VALID_ENV_MODES = {"yes", "no", "together", "fallback"}

    for data_key, data_spec in data_files.items():
        if not isinstance(data_spec, dict):
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}]: Muss ein Mapping sein, "
                f"nicht {type(data_spec).__name__}"
            )

        required_data = {"source", "transform", "env"}
        missing_data = sorted(required_data - set(data_spec.keys()))
        if missing_data:
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}]: Erforderliche Keys fehlen: "
                f"{', '.join(missing_data)}"
            )

        # source Validierung
        source_val = data_spec.get("source")
        if source_val not in _VALID_SOURCES:
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}].source: Ungültig, "
                f"muss einer dieser Werte sein: {', '.join(sorted(_VALID_SOURCES))}. "
                f"Erhalten: {source_val!r}"
            )

        # transform Validierung
        transform_val = data_spec.get("transform")
        if transform_val not in _VALID_TRANSFORMS:
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}].transform: Ungültig, "
                f"muss einer dieser Werte sein: {', '.join(sorted(_VALID_TRANSFORMS))}. "
                f"Erhalten: {transform_val!r}"
            )

        # env Validierung (inkl. bool-Normalisierung)
        env_val = data_spec.get("env")
        if isinstance(env_val, bool):
            env_normalized = "yes" if env_val else "no"
        else:
            env_normalized = str(env_val).strip().lower() if env_val else None

        if env_normalized not in _VALID_ENV_MODES:
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}].env: Ungültig, "
                f"muss einer dieser Werte sein: {', '.join(sorted(_VALID_ENV_MODES))}. "
                f"Erhalten: {env_val!r}"
            )

        # file Validierung (optional)
        file_val = data_spec.get("file")
        if file_val is not None:
            if not isinstance(file_val, str):
                raise EnvConfigValidationError(
                    f"{source}.data_files[{data_key!r}].file: Muss String sein, "
                    f"nicht {type(file_val).__name__}"
                )
            if env_normalized == "fallback":
                raise EnvConfigValidationError(
                    f"{source}.data_files[{data_key!r}]: "
                    f"'file' wird bei env='fallback' nicht unterstützt"
                )

        # targets Validierung (optional, Standard: ["*"])
        targets_val = data_spec.get("targets", ["*"])
        if not isinstance(targets_val, (list, tuple)):
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}].targets: Muss Liste/Tupel sein, "
                f"nicht {type(targets_val).__name__}"
            )
        if not targets_val:
            raise EnvConfigValidationError(
                f"{source}.data_files[{data_key!r}].targets: Darf nicht leer sein"
            )
        for idx, target in enumerate(targets_val):
            if not isinstance(target, str):
                raise EnvConfigValidationError(
                    f"{source}.data_files[{data_key!r}].targets[{idx}]: "
                    f"Muss String sein, nicht {type(target).__name__}"
                )


if __name__ == "__main__":
    import sys
    import yaml

    if len(sys.argv) < 2:
        print("Nutzung: python -m yaml_config_support.env_validator <path-to-env.yaml>")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"Fehler: Datei nicht gefunden: {config_path}")
        sys.exit(1)

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        validate_env_config(config, config_path)
        print(f"✓ Konfiguration ist gültig: {config_path}")
    except Exception as e:
        print(f"✗ Validierungsfehler: {e}")
        sys.exit(1)

