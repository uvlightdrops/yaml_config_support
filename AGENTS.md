# AGENTS.md – yaml_config_support Guide

## Purpose

`yaml_config_support` ist eine Python-Bibliothek zum **deklarativen Zusammensetzen von YAML-Konfigurationen** aus:
- einem öffentlichen **Base-Template** (`values_onefitsall.yaml`)
- mehreren **Overlay-Dateien** (z.B. aus `private/`, `project/`)
- mit verschiedenen **Transformationsstrategien**

Ziel: **Trennung von Template (Repo) und geheimen/lokalen Werten (außerhalb Repo)**.

---

## Zentrale Entitäten

### `yaml_config_support/cli_config_fill.py`
CLI-Einstiegspunkt. Koordiniert:
- Laden von `FillOptions` (Pfade, Umgebungen, `data_files`)
- Aufruf von `k8sValuesFill`
- Output nach `outdir/cf-<env>/updated_values-<env>.yaml`

### `yaml_config_support/k8sValuesFill.py`
Kernlogik:
1. Basis-Template laden
2. Overlay-Dateien in `data_files`-Reihenfolge laden
3. Pro Datei Transformationsstrategie anwenden
4. Ergebnis schreiben

### `yaml_config_support/yamlTemplateFillSupport.py`
Zwei Fill-Strategien:
- **`fill_config_template`**: rekursive Dict-Überlagerung (deep merge)
- **`fill_simple_template`**: Punktpfad-Keys + Listen-Updates

### `yaml_config_support/config_models.py`
Strukturierte Optionen:
- `FillOptions`: Template-Dir, ValueStore-Dir, Umgebungen, Output-Dir
- `DataFileSpec`: source/transform/env pro Overlay

### `scripts/cli_yaml_config_fill.py`
Projektspezifischer Wrapper mit Defaults:
- `default_template_dir`
- `default_valuestore_dir`
- `data_files` Mapping
- Output-Pfade

---

## Ablauf (Schritt für Schritt)

```
1. Basis-Templates laden (oder auto-collect aus template_collect_dir)
   templates/values_onefitsall.yaml
   oder: k8s/overlays/manual/*.yaml

2. Für jeden Eintrag in data_files (geordnet):
   a. Datei aus source laden
   b. Transformationsstrategie anwenden
   c. Ergebnis mergen pro Template

3. Finale YAML-Dateien schreiben:
   - single/concat: eine Datei
   - per_template: mehrere Dateien (eine pro Template)
```

### Dateinamenskonventionen

| `env` | Muster | Beispiel |
|---|---|---|
| `yes` | `values_<key>_<env>.yaml` | `values_creds_dev.yaml` |
| `no` | `values_<key>.yaml` | `values_user.yaml` |
| `together` | `values_<key>.yaml` (mit Env-Keys drin) | `values_creds.yaml` |

---

## `data_files` Schema

```python
data_files = {
    "creds": {
        "source": "private",           # oder "project"
        "transform": "fill_config_template",  # oder "fill_simple_template"
        "env": "yes",                  # oder "no", "together", "fallback"
    },
    "resources": {
        "source": "project",
        "transform": "fill_simple_template",
        "env": "together",
    },
}
```

**Wichtig**: Die Reihenfolge bestimmt die Merge-Reihenfolge!

---

## NEU: `template_collect_dir` Feature

Automatisches Sammeln aller YAML-Dateien aus einem Overlay-Verzeichnis:

```python
options = {
    "default_template_dir": "k8s",
    "default_valuestore_dir": "private",
    "template_collect_dir": "k8s/overlays/manual",  # NEU: Auto-collect *.yaml
    "data_files": { ... },
}
```

**Verhalten:**
- Sammelt alle `.yaml` / `.yml` Dateien aus dem Verzeichnis
- Sortiert alphabetisch
- Lädt im `per_template` Modus (separat, pro Template)
- Schreibt separate Output-Dateien pro Template

**Vorher (manuell):**
```python
"template_files": ["deploy-a.yaml", "deploy-b.yaml", "deploy-c.yaml"],
```

**Nachher (auto):**
```python
"template_collect_dir": "k8s/overlays/manual",
```

Siehe auch: `docs/admin/TEMPLATE_COLLECT_FEATURE.md`

---

## CLI-Nutzung

```bash
# Dev-Umgebung mit Defaults
python scripts/cli_yaml_config_fill.py dev

# Prod mit Output-Override
python scripts/cli_yaml_config_fill.py prod --outdir /tmp/generated

# Hilfe
python scripts/cli_yaml_config_fill.py --help
```

---

## Kombinierter Workflow: cli_yaml_config_fill → kustomize build

Für **saubere Separation**:

1. **cli_yaml_config_fill** ersetzt alle sensitiven/lokalen Werte in YAMLs
2. Gefüllte YAMLs landen in Arbeitsverzeichnis
3. **kustomize build** (oder kubectl kustomize) auf die gefüllten YAMLs anwenden
4. Multi-Doc YAML in `ready2apply/` schreiben

**Vorteil**: kein `csplit`-Overhead, alle Ressourcen schon gefüllt, saubere Human-Readability.

---

## Tests

```bash
# Discover-Lauf
python -m unittest discover -s tests -v

# Mit Temp-Dirs behalten
KEEP_TEST_TEMPDIRS=1 python -m unittest discover -s tests -v
```

---

## Bekannte Patterns

- **Basis-Templates im Repo**: `templates/values_onefitsall.yaml` ✅
- **Sensitive Overlays außerhalb Repo**: `private/values_creds_dev.yaml` (gitignored) ✅
- **Umgebungs-Varianz**: Mit `env: "yes"` oder `env: "together"` ✅
- **Merge-Reihenfolge**: `data_files` Dict-Order bestimmt Overlay-Reihenfolge ✅

