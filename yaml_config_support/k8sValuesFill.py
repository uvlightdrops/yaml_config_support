"""Lädt Wertedateien und kombiniert sie zu einer finalen Kubernetes-Values-Datei."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import shutil

import yaml

from .config_models import FillOptions
from .exceptions import EmptyYamlFileError, MissingEnvironmentError, YamlFileAccessError
from .yamlTemplateFillSupport import YamlTemplateFillSupport


class K8sValuesFill(YamlTemplateFillSupport):
    """Orchestriert das Laden, Überlagern und Schreiben von Values-Dateien.

    Die Klasse erwartet ein Basistemplate namens ``values_onefitsall.yaml`` im
    Template-Verzeichnis. Weitere Dateien werden über ``data_files`` beschrieben.
    Deren Reihenfolge bestimmt auch die Reihenfolge der Overlays.
    """

    template_file_name = "values_onefitsall.yaml"

    def __init__(self, env, template_dir, creds_dir, options):
        """Initialisiert den Füllprozess für eine Zielumgebung.

        Args:
            env: Zielumgebung wie ``dev`` oder ``prod``.
            template_dir: Verzeichnis mit Template- und Projektdateien.
            creds_dir: Verzeichnis mit privaten Wertedateien.
            options: Konfigurationsdictionary oder :class:`FillOptions`.
        """
        self.options = options if isinstance(options, FillOptions) else FillOptions.from_mapping(options)
        super().__init__(verbose=self.options.verbose)
        self.template_file_name = self.options.template_file_name
        self.template_files = self.options.template_files
        self.template_dir = Path(template_dir)
        self.creds_dir = Path(creds_dir)
        self.env = env
        self.data_files = self.options.data_files
        self.data = OrderedDict()
        self.template = {}
        self.result = {}

    def _read_yaml_file(self, file_path):
        """Liest eine YAML-Datei und liefert den geparsten Inhalt zurück.

        Args:
            file_path: Pfad zur Datei.

        Returns:
            Das aus YAML geladene Python-Objekt.

        Raises:
            YamlFileAccessError: Wenn die Datei nicht gelesen werden kann.
        """
        file_path = Path(file_path)
        self.out("READING", str(file_path))
        try:
            with file_path.open("r", encoding="utf-8") as file_handle:
                payload = yaml.safe_load(file_handle)
        except FileNotFoundError as exc:
            raise YamlFileAccessError(f"YAML-Datei nicht gefunden: {file_path}") from exc
        if payload is None:
            raise EmptyYamlFileError(f"YAML-Datei ist leer: {file_path}")
        return payload

    def _resolve_source_dir(self, spec):
        """Bestimmt das Stammverzeichnis für eine Dateispezifikation."""
        if spec.source == "private":
            return self.creds_dir
        return self.template_dir

    def _load_data_file(self, spec):
        """Lädt eine einzelne Overlay-Datei gemäß ihrer Spezifikation.

        Bei ``env == 'together'`` wird nur der Abschnitt der aktuellen Umgebung
        zurückgegeben.

        Bei ``env == 'fallback'`` wird zuerst ``values_<name>_<env>.yaml`` gesucht;
        existiert diese nicht, wird ``values_<name>.yaml`` als Fallback geladen.
        """
        source_dir = self._resolve_source_dir(spec)

        if spec.env == "fallback":
            for fname in spec.file_names(self.env):
                file_path = source_dir / fname
                if file_path.exists():
                    self.out("FALLBACK loading:", str(file_path))
                    return self._read_yaml_file(file_path)
            tried = ", ".join(spec.file_names(self.env))
            raise YamlFileAccessError(
                f"Keine Datei für '{spec.name}' gefunden. Gesucht: {tried} in {source_dir}"
            )

        file_path = source_dir / spec.file_name(self.env)
        payload = self._read_yaml_file(file_path)
        if spec.env != "together":
            return payload
        if self.env not in payload:
            raise MissingEnvironmentError(
                f"Umgebung {self.env!r} fehlt in Datei {file_path}"
            )
        return payload[self.env]

    def _resolve_file_path(self, spec):
        """Berechnet den konkreten Dateipfad für Daten- oder Template-Spezifikationen."""
        base_dir = self._resolve_source_dir(spec)
        if hasattr(spec, "path"):
            return base_dir / spec.path
        return base_dir / spec.file_name(self.env)

    def load_template_files(self):
        """Lädt eine oder mehrere Template-Dateien und kombiniert sie in Reihenfolge."""
        first_spec, *overlay_specs = self.template_files
        template_path = self._resolve_file_path(first_spec)
        current_template = self._read_yaml_file(template_path)
        self.out("TEMPLATE file:", str(template_path))

        for spec in overlay_specs:
            overlay_path = self._resolve_file_path(spec)
            overlay = self._read_yaml_file(overlay_path)
            self.out("TEMPLATE overlay:", str(overlay_path))
            current_template = self._apply_transform(current_template, spec, overlay)

        self.template = current_template
        return current_template

    def _apply_transform(self, template, spec, overlay):
        """Wendet die konfigurierte Transformationsstrategie auf ein Overlay an."""
        if spec.transform == "fill_config_template":
            return self.fill_config_template(template, overlay)
        if spec.transform == "fill_simple_template":
            return self.fill_simple_template(template, overlay)
        return template

    def load_files_spec(self):
        """Lädt alle in ``data_files`` beschriebenen Overlay-Dateien."""
        self.data = OrderedDict(
            (name, self._load_data_file(spec))
            for name, spec in self.data_files.items()
        )

    def load_files(self):
        """Lädt das Basistemplate und anschließend alle Overlay-Dateien."""
        self.load_template_files()
        self.load_files_spec()

    def fill_configs(self):
        """Wendet alle konfigurierten Overlays in definierter Reihenfolge an."""
        current_template = self.template
        for name, spec in self.data_files.items():
            overlay = self.data[name]
            current_template = self._apply_transform(current_template, spec, overlay)
        self.template = current_template
        self.result = current_template

    def build_output_path(self, out_dir, env=None):
        """Berechnet den Zielpfad der generierten Values-Datei.
        
        Der Ausgabedateiname wird vom ersten Template-Dateinamen abgeleitet,
        mit Umgebungs-Suffix ergänzt. Beispiel:
        - Input: deploy-wls-admin.yaml
        - Output: deploy-wls-admin-dev.yaml
        """
        target_env = env or self.env
        out_dir = Path(out_dir)
        
        # Hole Template-Dateinamen vom ersten Template
        if hasattr(self.template_files[0], 'path'):
            base_template_path = self.template_files[0].path
        else:
            base_template_path = str(self.template_files[0])
        
        # Entferne .yaml und füge -<env>.yaml hinzu
        base_name = Path(base_template_path).stem  # z.B. "deploy-wls-admin"
        output_filename = f"{base_name}-{target_env}.yaml"
        
        return out_dir / output_filename

    def write_output(self, out_dir, env):
        """Schreibt die berechnete Values-Datei in das Ausgabeziel.

        Die Ausgabe erfolgt nach ``<out_dir>/<base_template_name>-<env>.yaml``.
        Der Name wird vom Template-Namen abgeleitet (z.B. deploy-wls-admin.yaml 
        → deploy-wls-admin-dev.yaml).
        Existiert die Datei bereits, wird vor dem Überschreiben eine Sicherung
        ``*_bak.yaml`` angelegt.

        Args:
            out_dir: Basisverzeichnis für die Ausgabe.
            env: Name der Zielumgebung; wird im Dateinamen verwendet.
        """
        out_path = self.build_output_path(out_dir, env)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists():
            if self.verbose:
                print(f"Target output file existed: {out_path}, making backup")
            backup_path = Path(f"{out_path}_bak.yaml")
            shutil.copy(out_path, backup_path)

        with out_path.open("w", encoding="utf-8") as file_handle:
            yaml.dump(self.result, file_handle, default_flow_style=False, sort_keys=False)
        print("Completed config_values file written to", out_path)
        return out_path

    def run(self, out_dir):
        """Führt den vollständigen Workflow vom Laden bis zum Schreiben aus."""
        self.load_files()
        self.fill_configs()
        return self.write_output(out_dir, self.env)
