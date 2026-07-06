# Quickstart: yaml_config_support Setup

## Installation & Vorbereitung

### 1. Konfigurationsdatei erstellen

Kopiere das Beispiel-Template zu deinem Projekt:

```bash
cd /home/flow/dev_mk/ansible_mk
cp ~/dev_flow/yaml_config_support/scripts/env.example_ansible_mk.py env.py
```

Bearbeite `env.py` und passe Pfade an (wenn nötig):
- `project_base` – Root deines Kubernetes-Projekts
- `valuestore_dir` – Wo deine gitignored `private/` Werte-Dateien liegen
- `outpath` – Wo gefüllte YAMLs landen (z.B. `ready2apply/`)

### 2. Optional: Umgebungsvariablen setzen

Kopiere `.env.example`:

```bash
cp .env.example .env
```

Typische Vars:
- `PYTHON_BIN=python3.11` – Falls dein Default nicht passt
- `KEEP_TEST_TEMPDIRS=1` – Tests auf Fehlersuche behalten

### 3. CLI ausführen

Aus der `env.py` Verzeichnis (oder von überall mit `--template_dir` Override):

```bash
python3 ~/dev_flow/yaml_config_support/scripts/cli_yaml_config_fill.py dev
```

Oder mit Output-Override:

```bash
python3 ~/dev_flow/yaml_config_support/scripts/cli_yaml_config_fill.py prod --outdir /tmp/rendered
```

## Workflow-Phasen

### Phase 1: Template-Fill (dein Tool)

```bash
python3 scripts/cli_yaml_config_fill.py dev
# → `ready2apply/` enthält gefüllte YAMLs mit echten Werten
```

### Phase 2: Kustomize-Render (optional, Kubernetes-Struktur)

```bash
cd ready2apply
kustomize build ../k8s/overlays/manual > manual-no-operator.rendered.yaml
```

### Phase 3: Deploy (nur kubectl)

```bash
kubectl apply -f manual-no-operator.rendered.yaml
```

## Struktur erklärung

```
ansible_mk/
├── env.py                    ← Deine lokale Config (NICHT committe!)
├── private/                  ← Gitignored Secrets
│   ├── values_creds_dev.yaml
│   └── values_creds_prod.yaml
├── k8s/
│   └── overlays/manual/      ← Template-Quelle (auto-collected)
│       ├── deploy-wls-admin.yaml
│       ├── deploy-wls-managed-1.yaml
│       └── kustomization.yaml
└── ready2apply/              ← Gefüllte YAMLs (gitignored)
    └── manual-no-operator.rendered.yaml
```

## Troubleshooting

### „ModuleNotFoundError: No module named 'yaml_config_support'"

Stelle sicher, dass `~/dev_flow/yaml_config_support` existiert und im `sys.path` ist. Der CLI-Wrapper `cli_yaml_config_fill.py` verwaltet das automatisch.

### „Overlay-Verzeichnis nicht gefunden: …"

Prüfe `env.py` – speziell `template_collect_dir`. Muss auf dein overlay-Verzeichnis zeigen (z.B. `k8s/overlays/manual`).

### Werte werden nicht ersetzt

1. Prüfe `values_*.yaml` im `private/`-Verzeichnis
2. Verifiziere Schlüsselnamen in Template vs. Werte-Datei
3. Nutze `--verbose` flag: `cli_yaml_config_fill.py dev --verbose`

## Test ausführen

```bash
cd ~/dev_flow/yaml_config_support
python3 -m unittest discover -s tests -v
```

Alle 17 Tests sollten bestehen.

