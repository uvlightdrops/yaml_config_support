# yaml-config-support

Hilfsbibliothek zum Füllen von YAML-Konfigurationen aus einem öffentlichen Template-Verzeichnis und getrennten, nicht öffentlichen Wertedateien.

Der Schwerpunkt dieses Repositories liegt aktuell auf dem Ablauf in `yaml_config_support/cli_config_fill.py` und `yaml_config_support/k8sValuesFill.py`:

- ein Basis-Template laden,
- mehrere Overlay-Dateien in definierter Reihenfolge einlesen,
- sensible und öffentliche Werte getrennt halten,
- eine finale `values.yaml`-ähnliche Datei erzeugen.

## Wofür ist das gedacht?

Das Muster ist nützlich, wenn du:

- ein gemeinsames YAML-Grundgerüst versionieren willst,
- geheime oder lokale Werte separat speichern möchtest,
- für mehrere Umgebungen (`dev`, `test`, `prod`) bauen willst,
- einzelne Werte entweder rekursiv oder per Punktpfad überschreiben möchtest.

## Zentrale Bausteine

- `yaml_config_support/cli_config_fill.py`  
  CLI-Einstiegspunkt. Erwartet ein `options`-Mapping oder `FillOptions` mit Standardpfaden und `data_files`.
- `yaml_config_support/k8sValuesFill.py`  
  Lädt Template und Overlay-Dateien und schreibt die Ergebnisdatei.
- `yaml_config_support/config_models.py`  
  Enthält die strukturierten Konfigurationsmodelle `FillOptions` und `DataFileSpec`.
- `yaml_config_support/yamlTemplateFillSupport.py`  
  Implementiert die zwei Füllstrategien:
  - `fill_config_template`: rekursive Dict-Überlagerung
  - `fill_simple_template`: Punktpfade und Listen-Updates
- `scripts/cli_yaml_config_fill.py`  
  Beispiel-Wrapper mit projektspezifischen Standardpfaden.

## Kurzüberblick über den Ablauf

1. `values_onefitsall.yaml` aus dem Template-Verzeichnis laden.
2. Für jeden Eintrag aus `data_files` die passende Datei laden.
3. Pro Datei die definierte Transformationsstrategie anwenden.
4. Ergebnis nach `<outdir>/cf-<env>/updated_values-<env>.yaml` schreiben.

## Schnellstart

### 1. Projektabhängigen Wrapper konfigurieren

Der einfachste Einstieg ist ein Wrapper wie `scripts/cli_yaml_config_fill.py`. Dort definierst du:

- `default_template_dir`
- `default_valuestore_dir`
- `outpath`
- `data_files`

### 2. CLI aufrufen

```bash
python scripts/cli_yaml_config_fill.py dev
python scripts/cli_yaml_config_fill.py prod --outdir /tmp/generated-values
```

### 3. Hilfe anzeigen

```bash
python scripts/cli_yaml_config_fill.py --help
```

## `data_files`-Schema

Jeder Eintrag beschreibt eine Overlay-Datei:

```python
data_files = {
    "creds": {
        "source": "private",
        "transform": "fill_config_template",
        "env": "yes",
    },
    "resources": {
        "source": "project",
        "transform": "fill_simple_template",
        "env": "together",
    },
    "user": {
        "source": "private",
        "transform": "fill_config_template",
        "env": "no",
    },
}
```

Bedeutung der Felder:

- `source`
  - `private`: Datei wird aus dem Value-Store gelesen
  - `project`: Datei wird aus dem Template-Verzeichnis gelesen
- `transform`
  - `fill_config_template`: rekursive Dict-Überlagerung
  - `fill_simple_template`: Punktpfade und `lists`
- `env`
  - `yes`: Dateiname enthält die Umgebung, z. B. `values_creds_dev.yaml`
  - `no`: Dateiname ist umgebungsunabhängig, z. B. `values_user.yaml`
  - `together`: Datei enthält mehrere Umgebungen als Ober-Schlüssel; es wird `tmp[self.env]` verwendet

> Die Reihenfolge der Einträge in `data_files` ist wichtig, weil genau diese Reihenfolge die Overlays bestimmt.

## Dateinamenskonventionen

### Basis-Template

```text
template_dir/values_onefitsall.yaml
```

### Overlay-Dateien

Für einen Schlüssel `<key>` in `data_files` werden folgende Muster verwendet:

- bei `env == "yes"`: `values_<key>_<env>.yaml`
- bei `env == "no"`: `values_<key>.yaml`
- bei `env == "together"`: `values_<key>.yaml`

## Tutorial

Die ausführliche Schritt-für-Schritt-Anleitung findest du in:

- `docs/tutorial_cli_config_fill.md`

## Entwicklung und Qualität

Die Projektstruktur wurde bewusst in klarere Zuständigkeiten aufgeteilt:

- strukturierte Optionsmodelle statt impliziter Dict-Manipulation,
- `pathlib` statt String-Pfadverkettung,
- klarere Ausnahmen bei fehlenden YAML-Dateien oder Umgebungen,
- Unittests für Template-Füllung und End-to-End-Workflow.

### Tests ausführen

```bash
python -m unittest discover -s tests -v
```

### Temporäre Testverzeichnisse behalten

Für den normalen Discover-Lauf:

```bash
KEEP_TEST_TEMPDIRS=1 python -m unittest discover -s tests -v
```

Für den direkten Aufruf von `tests/test_k8s_values_fill.py` gibt es zusätzlich
ein Flag:

```bash
python tests/test_k8s_values_fill.py --keep-tempdirs
```

Wenn der Schalter aktiv ist, wird der Pfad des temporären Testverzeichnisses
ausgegeben und am Ende nicht gelöscht.

## Bekannte Hinweise

- Das Paket enthält zusätzlich `YamlConfigSupport`, das eine andere YAML-Konfigurationslogik abdeckt. Das Tutorial hier beschreibt gezielt den Template-Fill-Ablauf.

