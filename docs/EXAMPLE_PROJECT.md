# Beispiel-Projekt Setup

Dieses Verzeichnis zeigt, wie du dein Projekt strukturiert aufbaust.

## Struktur

```
mein_projekt/
├── k8s/                           # template_dir
│   ├── deploy-wls-admin.yaml      # Basis-Template
│   ├── deploy-wls-managed-1.yaml  # (weitere Templates optional)
│   └── values_resources.yaml      # Umgebungs-Werte (env: together)
├── secrets/                       # valuestore_dir
│   ├── values_creds_dev.yaml      # Secrets für dev
│   ├── values_creds_prod.yaml     # Secrets für prod
│   └── values_user.yaml           # Nutzer-spezifische Werte
└── out/                           # outpath (wo Ausgaben landen)
```

## 1. Basis-Template erstellen

**Datei: `k8s/deploy-wls-admin.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: weblogic
data:
  LOG_LEVEL: "info"
  REPLICAS: "2"
  IMAGE_TAG: "latest"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wls-admin
  namespace: weblogic
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wls-admin
  template:
    metadata:
      labels:
        app: wls-admin
    spec:
      containers:
      - name: weblogic
        image: weblogic:latest
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
        env:
        - name: WL_HOME
          value: /u01/oracle/wlserver
```

## 2. Werte-Dateien für verschiedene Umgebungen

### Option A: `env: "together"` (empfohlen)

**Datei: `k8s/values_resources.yaml`**

```yaml
dev:
  spec.replicas: 2
  spec.template.spec.containers[0].image: weblogic:dev
  spec.template.spec.containers[0].resources.limits.cpu: 200m
  spec.template.spec.containers[0].resources.limits.memory: 256Mi
prod:
  spec.replicas: 5
  spec.template.spec.containers[0].image: weblogic:prod
  spec.template.spec.containers[0].resources.limits.cpu: 500m
  spec.template.spec.containers[0].resources.limits.memory: 512Mi
staging:
  spec.replicas: 3
  spec.template.spec.containers[0].image: weblogic:staging
  spec.template.spec.containers[0].resources.limits.cpu: 300m
  spec.template.spec.containers[0].resources.limits.memory: 384Mi
```

### Option B: `env: "yes"` (Dateiname mit Umgebung)

**Datei: `secrets/values_creds_dev.yaml`**
```yaml
metadata:
  namespace: weblogic-dev
data:
  DB_USER: dev_user
  DB_HOST: localhost
```

**Datei: `secrets/values_creds_prod.yaml`**
```yaml
metadata:
  namespace: weblogic-prod
data:
  DB_USER: prod_user
  DB_HOST: prod-db.example.com
```

### Option C: `env: "no"` (eine Datei für alle)

**Datei: `secrets/values_user.yaml`**
```yaml
metadata:
  labels:
    managed-by: admin
    version: "1.0"
```

---

## 3. scripts/env.py konfigurieren

```python
from collections import OrderedDict
from pathlib import Path

home_dir = Path.home()
project_subpath = "mein_projekt"       # ← Dein Projekt-Ordner
target_env = "dev"                     # ← Umgebung wechseln: dev, prod, staging
basedir = home_dir / project_subpath
template_dir = basedir / "k8s"
valuestore_dir = basedir / "secrets"
outpath = basedir / "out"

# Template-Dateien
template_file_name = "deploy-wls-admin.yaml"
template_defaults = {
    "source": "project",
    "transform": "fill_simple_template",
}
template_files = [template_file_name]

# Werte-Dateien
data_file_defaults = {
    "source": "project",
    "transform": "fill_simple_template",
    "env": "together",  # Alle Umgebungen in einer Datei
}

data_files = OrderedDict([
    ("resources", {}),  # erbt template_defaults
    ("creds", {
        "source": "private",  # Im secrets/ Verzeichnis
        "env": "yes",         # Separate Datei pro Umgebung
    }),
    ("user", {
        "source": "private",
        "env": "no",          # Gleiche Datei für alle Umgebungen
    }),
])
```

---

## 4. Ausführen

```bash
cd /home/flow/dev_flow/yaml_config_support
python3 scripts/cli_yaml_config_fill.py
```

**Ergebnis:**
```
mein_projekt/out/deploy-wls-admin-dev.yaml
```

Der Dateiname wird automatisch vom Template abgeleitet.

---

## 5. Verschiedene Umgebungen generieren

Um Prod zu generieren, ändere `scripts/env.py`:

```python
target_env = "prod"  # war "dev"
```

Dann:
```bash
python3 scripts/cli_yaml_config_fill.py
```

**Ergebnis:**
```
mein_projekt/out/deploy-wls-admin-prod.yaml
```

---

## 6. Im Kubernetes deployen

```bash
# Dev deployen
kubectl apply -f mein_projekt/out/deploy-wls-admin-dev.yaml

# Prod deployen
kubectl apply -f mein_projekt/out/deploy-wls-admin-prod.yaml
```

---

## Weitere Hinweise

- **Basis-Template sollte vollständig sein**: Alle Felder, die es geben könnte, sollten im Template angelegt sein (mit Default-Werten)
- **Werte-Dateien ergänzen**: Sie überschreiben nur vorhandene Werte
- **Reihenfolge zählt**: Wenn mehrere Werte-Dateien auf denselben Pfad schreiben, gewinnt die letzte in der `data_files`-Liste

