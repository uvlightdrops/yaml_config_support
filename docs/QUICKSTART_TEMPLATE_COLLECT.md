# Quick Start: Template Collect für K8s Overlays

## 5-Minuten Übersicht

Die neue `template_collect_dir` Option macht es **extrem einfach**, alle YAML-Dateien aus `k8s/overlays/<overlay>/` automatisch zu sammeln, zu füllen und auszugeben.

---

## Setup

### 1. `env.py` aktualisieren

```python
# OLD: Manuelle Liste
# template_files = ["deployment.yaml", "service.yaml"]

# NEW: Automatisches Sammeln
template_collect_dir = "k8s/overlays/manual"  # oder "k8s/overlays/prod", etc.
```

Das war's! 🎉

### 2. CLI Aufruf (wie zuvor)
```bash
python scripts/cli_yaml_config_fill.py dev --overlay manual
```

---

## Ergebnis

### Struktur
```
k8s/overlays/manual/
├── deployment.yaml
├── service.yaml
└── configmap.yaml
```

### Output
```
out/
├── deployment-dev.yaml      (gefüllt)
├── service-dev.yaml         (gefüllt)
└── configmap-dev.yaml       (gefüllt)
```

---

## Praktischer Workflow

### Schritt 1: Alle YAMLs füllen
```bash
python scripts/cli_yaml_config_fill.py dev --overlay manual
```

**Output:**
```
Completed config_values file written to out/deployment-dev.yaml
Completed config_values file written to out/service-dev.yaml
Completed config_values file written to out/configmap-dev.yaml
```

### Schritt 2: Mit Kustomize kombinieren (optional)
```bash
kustomize build out/ > ready2apply/manifest-dev.yaml
```

### Schritt 3: Anwenden
```bash
kubectl apply -f ready2apply/manifest-dev.yaml
```

---

## Beispiel env.py

```python
#!/usr/bin/env python3

from pathlib import Path
from collections import OrderedDict

# Verzeichnis-Definitionen
basedir = str(Path(__file__).parent)
template_dir = f"{basedir}/k8s"
valuestore_dir = f"{basedir}/private"
outpath = f"{basedir}/out"

# Zielumgebung (Standard)
target_env = "dev"

# Overlay-Verzeichnis mit allen YAMLs
template_collect_dir = f"{basedir}/k8s/overlays/manual"

# Daten-Overlays: Geheimnisse und Konfigurationen
data_files = OrderedDict([
    ("creds", {
        "source": "private",
        "transform": "fill_config_template",
        "env": "yes",
    }),
    ("resources", {
        "source": "project",
        "transform": "fill_simple_template",
        "env": "together",
    }),
])

# Optionale Defaults
data_file_defaults = {
    "source": "project",
    "transform": "fill_config_template",
    "env": "no",
}

template_defaults = {
    "source": "project",
    "transform": "fill_config_template",
}
```

---

## Vorher vs. Nachher

### Vorher (template_files)

```python
# Manuell jede Datei aufzählen
template_files = [
    "deployment.yaml",
    "service.yaml",
    "statefulset.yaml",
    "configmap.yaml",
    "secret.yaml",
    # 👎 Fehler anfällig: neue Dateien vergessen
]
```

### Nachher (template_collect_dir)

```python
# Automatisch alle *.yaml aus Verzeichnis
template_collect_dir = "k8s/overlays/manual"
# 👍 Skalierbar: neue Dateien autom. erfasst
```

---

## Häufige Fragen

### F: Was ist der Unterschied zwischen `template_collect_dir` und `template_files`?

| Feature | `template_files` | `template_collect_dir` |
|---|---|---|
| Konfiguration | Manuell | Automatisch |
| Neue Dateien | Manuell hinzufügen | Autom. erfasst |
| Fehleranfälligkeit | Hoch | Niedrig |
| Best-Practice | Für spezifische Auswahl | Für Overlays |

### F: Kann ich beide zusammen nutzen?

**Nein.** Wenn `template_collect_dir` gesetzt ist, wird `template_files` ignoriert.

### F: In welcher Reihenfolge werden Dateien geladen?

Alphabetisch sortiert:
```
configmap.yaml    (1)
deployment.yaml   (2)
secret.yaml       (3)
service.yaml      (4)
```

### F: Funktioniert es mit Unterverzeichnissen?

**Nein.** Nur Top-Level Dateien im Verzeichnis.

**Lösung:** Lege alle YAMLs flach im `template_collect_dir` ab.

### F: Kann ich auch `.yml` Dateien verwenden?

**Ja!** Beide `.yaml` und `.yml` werden erfasst.

---

## Vollständiges Beispiel: ansible_mk Integration

### Verzeichnis-Struktur
```
/home/flow/dev_mk/ansible_mk/
├── env.py
├── k8s/
│   ├── overlays/
│   │   ├── manual/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   └── prod/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   └── kustomization.yaml
├── private/
│   ├── values_creds_dev.yaml
│   ├── values_creds_prod.yaml
│   └── values_resources.yaml
└── out/
    ├── deployment-dev.yaml    (generiert)
    ├── service-dev.yaml       (generiert)
    └── configmap-dev.yaml     (generiert)
```

### env.py Konfiguration

```python
basedir = "/home/flow/dev_mk/ansible_mk"
template_dir = f"{basedir}/k8s"
valuestore_dir = f"{basedir}/private"
outpath = f"{basedir}/out"
target_env = "dev"

# Automatisch alle YAMLs aus dem Overlay sammeln
template_collect_dir = f"{template_dir}/overlays/manual"

data_files = OrderedDict([
    ("creds", {
        "source": "private",
        "transform": "fill_config_template",
        "env": "yes",
    }),
])
```

### CLI Nutzung

```bash
# 1. Dev-Umgebung mit manual-Overlay
python scripts/cli_yaml_config_fill.py dev --overlay manual
# Output: out/deployment-dev.yaml, out/service-dev.yaml, out/configmap-dev.yaml

# 2. Prod-Umgebung mit prod-Overlay
python scripts/cli_yaml_config_fill.py prod --overlay prod
# Output: out/deployment-prod.yaml, out/service-prod.yaml

# 3. Kustomize auf gefüllte Dateien anwenden
kustomize build out/ > ready2apply/manifest-dev.yaml

# 4. Anwenden
kubectl apply -f ready2apply/manifest-dev.yaml
```

---

## Tipps & Tricks

### Tip 1: Konvention einhalten
Nutze beschreibende Namen für Dateien:
```
deployment.yaml    ✅ Klar
service.yaml       ✅ Klar
configmap.yaml     ✅ Klar
x.yaml             ❌ Unklar
```

### Tip 2: Sortierung nutzen
Dateinamen-Reihenfolge bestimmt Lade-Reihenfolge. Nutze Präfixe für explizite Reihenfolge:
```
01-configmap.yaml      (wird zuerst geladen)
02-deployment.yaml
03-service.yaml
04-ingress.yaml        (wird zuletzt geladen)
```

### Tip 3: Mit .yml und .yaml mischen
```
deployment.yaml
service.yml           (auch OK!)
configmap.yaml
```
Beides funktioniert.

### Tip 4: Debugging
```bash
# Mit --verbose Output sehen
python scripts/cli_yaml_config_fill.py dev -v --overlay manual

# Oder:
export VERBOSE=1
python scripts/cli_yaml_config_fill.py dev --overlay manual
```

---

## Troubleshooting

### Fehler: `template_collect_dir existiert nicht`

**Ursache:** Der Pfad ist falsch.

**Lösung:**
```python
# Prüfe den Pfad
import os
print(os.path.exists(template_collect_dir))  # Sollte True sein
```

### Fehler: `Keine YAML-Dateien in ... gefunden`

**Ursache:** Das Verzeichnis ist leer.

**Lösung:**
```bash
ls -la k8s/overlays/manual/
# Sollte mindestens eine .yaml Datei zeigen
```

### Output-Dateien haben falsche Namen

**Standard Output-Format:**
```
<template-name>-<env>.yaml
```

**Beispiel:**
- Input: `deployment.yaml` + env `dev`
- Output: `deployment-dev.yaml`

**Bei absoluten Pfaden:**
Stellen Sie sicher, dass `template_collect_dir` relativ oder absolut konsistent ist.

---

## Zusammenfassung

✅ **Vorteile der `template_collect_dir` Feature:**
1. **Einfacher**: Keine manuelle Dateilisten nötig
2. **Skalierbar**: Neue Dateien autom. erfasst
3. **Sortiert**: Alphabetische Reihenfolge (vorhersehbar)
4. **Kustomize-Ready**: Output direkt für kustomize nutzbar
5. **Backward-Kompatibel**: Alte Konfigurationen funktionieren noch

🚀 **Los geht's:**
```bash
python scripts/cli_yaml_config_fill.py dev --overlay manual
```

