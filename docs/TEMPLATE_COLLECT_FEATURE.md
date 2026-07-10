# Template Collect Feature

## Übersicht

Die neue Option **`template_collect_dir`** ermöglicht es, **alle YAML-Dateien aus einem Verzeichnis automatisch zu sammeln** und sie sequenziell mit den konfigurierten `data_files`-Overlays zu füllen.

Dies vereinfacht den Workflow erheblich, wenn mehrere Manifeste (z. B. aus `k8s/overlays/manual/`) gefüllt und verarbeitet werden sollen.

---

## Syntax

### In `env.py`

```python
options = {
    "default_template_dir": "/path/to/k8s",
    "default_valuestore_dir": "/path/to/secrets",
    "outpath": "out",
    "template_collect_dir": "/path/to/k8s/overlays/manual",  # NEU
    "data_files": {
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
    },
}
```

---

## Verhalten

Wenn `template_collect_dir` gesetzt ist:

1. **Alle `.yaml` und `.yml` Dateien** aus dem Verzeichnis werden **alphabetisch sortiert** und geladen
2. Der Prozess läuft automatisch im **`per_template` Modus**
3. **Jede Datei** wird separat mit allen `data_files`-Overlays gefüllt
4. **Pro Template** wird eine **separate Output-Datei** geschrieben

### Beispiel

Verzeichnis-Struktur:
```
k8s/overlays/manual/
├── deployment.yaml
├── service.yaml
└── configmap.yaml
```

Mit `template_collect_dir: "/path/to/k8s/overlays/manual"`:

**Ablauf:**
1. Alle 3 Dateien werden geladen (sortiert)
2. Auf jede werden die Overlays aus `data_files` angewendet
3. Output wird in 3 separate Dateien geschrieben:
   - `out/deployment-dev.yaml`
   - `out/service-dev.yaml`
   - `out/configmap-dev.yaml`

---

## Backward-Kompatibilität

- **Wenn `template_collect_dir` NICHT gesetzt ist**, funktioniert alles wie zuvor
- **`template_files` wird ignoriert**, wenn `template_collect_dir` gesetzt ist
- Alle anderen Konfigurationen bleiben unverändert
- Alte `env.py` Dateien funktionieren ohne Änderungen

---

## Praktisches Beispiel: cli_yaml_config_fill.py

Der Wrapper-Script nutzt jetzt automatisch `template_collect_dir`:

```python
def build_options(overlay_name: str):
    dynamic_template_dir = Path(template_dir) / "overlays" / overlay_name
    return {
        "default_template_dir": dynamic_template_dir,
        "default_valuestore_dir": valuestore_dir,
        "outpath": outpath,
        "template_collect_dir": str(dynamic_template_dir),  # NEU
        "data_files": data_files,
    }
```

**Aufruf:**
```bash
# Sammelt alle YAMLs aus k8s/overlays/manual/
python scripts/cli_yaml_config_fill.py dev --overlay manual
```

---

## Workflow mit Kustomize

Kombiniert mit Kustomize für vollständige Automatisierung:

```bash
# 1. Alle Dateien in k8s/overlays/manual/ mit Secrets füllen
python scripts/cli_yaml_config_fill.py dev --overlay manual

# 2. Kustomize auf die gefüllten Dateien anwenden
kustomize build out/ > ready2apply/manifest-dev.yaml

# 3. Bereit zum Anwenden
kubectl apply -f ready2apply/manifest-dev.yaml
```

**Vorteil**: Keine separaten `csplit`-Aufrufe, alle Dateien sind bereits gefüllt und lesbar.

---

## Tests

Siehe `tests/test_k8s_values_fill.py::test_template_collect_dir_loads_all_yaml_files`:

```python
def test_template_collect_dir_loads_all_yaml_files(self):
    """template_collect_dir sammelt automatisch alle *.yaml Dateien aus einem Verzeichnis."""
    # ... Setup ...
    options["template_collect_dir"] = str(overlay_dir)
    fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
    fill.load_files()
    
    # Es sollten 2 Templates geladen sein (deployment.yaml, service.yaml)
    self.assertEqual(fill.template_mode, "per_template")
    self.assertEqual(len(fill.template), 2)
```

---

## Häufige Fehler

### Fehler: `template_collect_dir existiert nicht`

**Ursache:** Der Pfad existiert nicht oder ist nicht korrekt.

**Lösung:** Prüfe den Pfad:
```python
import os
print(os.path.exists("/path/to/k8s/overlays/manual"))
```

### Fehler: `Keine YAML-Dateien in ... gefunden`

**Ursache:** Das Verzeichnis ist leer oder enthält keine `.yaml`/`.yml` Dateien.

**Lösung:** 
- Stelle sicher, dass YAMLs im Verzeichnis vorhanden sind
- Verwende `*.yaml` oder `*.yml` Endungen

### Output-Dateien nicht im richtigen Verzeichnis

**Ursache:** `outpath` ist nicht richtig konfiguriert.

**Lösung:**
```python
"outpath": "out",  # oder absoluter Pfad
```

---

## Migration von `template_files` zu `template_collect_dir`

**Alt (template_files):**
```python
"template_files": ["deploy-a.yaml", "deploy-b.yaml", "deploy-c.yaml"],
```

**Neu (template_collect_dir):**
```python
"template_collect_dir": "/path/to/k8s/overlays/manual",  # Alle YAMLs automatisch
```

Die neue Methode ist:
- ✅ Weniger Konfiguration
- ✅ Skalierbar (neue YAMLs autom. erfasst)
- ✅ Sortiert (alphabetisch)
- ✅ Keine manuelle Verwaltung

