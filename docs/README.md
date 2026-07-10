# Technische Anleitung: YAML-Templates automatisch füllen

## Worum geht es?

Du hast eine **YAML-Konfigurationsdatei** (z. B. Kubernetes-Manifest), die für verschiedene Umgebungen unterschiedliche Werte braucht:

- **Dev**: Image `registry/app:dev`, 2 Replicas, Debug-Logging
- **Prod**: Image `registry/app:prod`, 5 Replicas, Error-Logging nur

Statt diese Datei manuell zu kopieren und zu bearbeiten, **generiert dieses Skript die finale Datei automatisch** aus:

1. **Basis-Template** (öffentlich, in Git)
2. **Werte-Dateien** (private/spezifische Werte, separat)

**Ergebnis**: Für jede Umgebung eine fertige Konfigurationsdatei – reproduzierbar und fehlerarm.

---

## Schnelleinstieg (5 Minuten)

### Schritt 1: Konfiguration anpassen

Öffne `scripts/env.py` in deinem Editor und ändere die Verzeichnisse auf deinen Projekt-Pfad:

```python
home_dir = Path.home()
project_subpath = "dev_ldbv"  # ← Dein Projekt-Ordner
target_env = "dev"             # ← Aktuell zu generierende Umgebung
basedir = home_dir / project_subpath / "k8s_weblogic"
template_dir = basedir / "k8s"
valuestore_dir = basedir
outpath = basedir / "out"
```

**Was bedeutet was?**

| Variable | Bedeutung |
|----------|-----------|
| `project_subpath` | Ordner deines Projekts (z. B. `my_project/`) |
| `target_env` | Umgebung, für die die Datei generiert wird (z. B. `dev`, `prod`) |
| `template_dir` | Ordner mit den Basis-Templates |
| `valuestore_dir` | Ordner mit den spezifischen Werte-Dateien |
| `outpath` | Ordner, wo die fertige Datei gespeichert wird |

### Schritt 2: Basis-Template vorbereiten

Erstelle im `template_dir` die Datei `deploy-wls-admin.yaml` mit deiner Standard-Konfiguration:

```yaml
# deploy-wls-admin.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: app
        image: registry/app:latest
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
```

### Schritt 3: Werte-Dateien erstellen

Für jede Umgebung erstellst du eine Werte-Datei mit den spezifischen Werten.

**Beispiel für `dev`:**

```yaml
# valuestore_dir/values_resources.yaml
dev:
  spec.replicas: 2
  spec.template.spec.containers[0].image: registry/app:dev
  spec.template.spec.containers[0].resources.limits.cpu: 200m
prod:
  spec.replicas: 5
  spec.template.spec.containers[0].image: registry/app:prod
  spec.template.spec.containers[0].resources.limits.cpu: 500m
```

### Schritt 4: Skript ausführen

```bash
cd /home/flow/dev_flow/yaml_config_support
python3 scripts/cli_yaml_config_fill.py
```

**Fertig!** Die Datei ist unter `outpath/deploy-wls-admin-dev.yaml` gespeichert.

Der Dateiname wird automatisch vom Template abgeleitet (z. B. `deploy-wls-admin.yaml` → `deploy-wls-admin-dev.yaml`).

---

## Dateistruktur verstehen

Die Struktur könnte so aussehen:

```
mein_projekt/
├── k8s/                           # template_dir
│   ├── deploy-wls-admin.yaml      # Basis-Template (öffentlich)
│   └── values_resources.yaml      # Umgebungs-Werte pro Env
├── values_creds_dev.yaml          # valuestore_dir
├── values_creds_prod.yaml
└── out/                           # outpath
    ├── deploy-wls-admin-dev.yaml      # ← Generierte Datei (Template-Name mit -env Suffix)
    └── deploy-wls-admin-prod.yaml
```

---

## Häufige Aufgaben

### Task 1: Für eine andere Umgebung generieren

Ändere in `scripts/env.py`:

```python
target_env = "prod"  # war "dev"
```

Dann führe das Skript erneut aus:

```bash
python3 scripts/cli_yaml_config_fill.py
```

### Task 2: Eine neue Werte-Datei hinzufügen

Öffne `scripts/env.py` und füge ein neues Element zu `data_files` hinzu:

```python
data_files = OrderedDict([
    ("resources", {...}),  # existierend
    ("secrets", {          # ← NEU
        "source": "project",
        "transform": "fill_simple_template",
        "env": "no",       # gleiche Datei für alle Environments
    }),
])
```

Erstelle dann die neue Werte-Datei:

```yaml
# valuestore_dir/values_secrets.yaml
database_password: super-secret
api_key: abc123def456
```

### Task 3: Die Struktur einer Werte-Datei verstehen

Es gibt zwei Strategien zum Einfügen von Werten:

#### A. `fill_config_template` – Strukturelles Merge

Wenn die Werte-Datei die **gleiche Struktur** wie das Template hat:

```yaml
# Template
database:
  host: localhost
  port: 5432
```

```yaml
# Werte-Datei
database:
  host: my-db-server.com
```

**Ergebnis**: 

```yaml
database:
  host: my-db-server.com
  port: 5432  # bleibt erhalten
```

#### B. `fill_simple_template` – Punkt-Notation

Wenn du gezielt einzelne Pfade setzen willst:

```yaml
# Werte-Datei
database.host: my-db-server.com
database.port: 3306
app.replicas: 5
```

Das setzt diese Pfade im Template.

### Task 4: Verschiedene Werte pro Umgebung

Es gibt drei Optionen:

#### Option 1: `env: "yes"` – Dateiname mit Umgebung

```python
data_files = OrderedDict([
    ("resources", {
        "env": "yes",  # ← Umgebung im Dateinamen
    }),
])
```

Du erstellst dann:
- `values_resources_dev.yaml` (für dev)
- `values_resources_prod.yaml` (für prod)
- `values_resources_staging.yaml` (für staging)

#### Option 2: `env: "no"` – Eine Datei für alle

```python
data_files = OrderedDict([
    ("resources", {
        "env": "no",  # ← Gleiche Datei für alle Umgebungen
    }),
])
```

Eine Datei `values_resources.yaml` wird für alle Umgebungen verwendet.

#### Option 3: `env: "together"` – Umgebungen in einer Datei

```python
data_files = OrderedDict([
    ("resources", {
        "env": "together",  # ← Alle Umgebungen in einer Datei
    }),
])
```

Datei `values_resources.yaml`:

```yaml
dev:
  app.replicas: 2
  app.image: registry/app:dev
prod:
  app.replicas: 5
  app.image: registry/app:prod
```

---

## Fehlerbehebung

### Fehler: `FileNotFoundError: values_resources.yaml not found`

**Ursache**: Die Werte-Datei existiert nicht.

**Lösung**:
1. Prüfe den Pfad in `scripts/env.py`
2. Erstelle die fehlende Datei im `valuestore_dir`

### Fehler: `MissingEnvironmentError: Umgebung 'prod' fehlt in Datei values_resources.yaml`

**Ursache**: Du hast `env: "together"` eingestellt, aber in der Datei gibt es keinen `prod:`-Block.

**Lösung**:
```yaml
# values_resources.yaml
dev:
  app.replicas: 2
prod:  # ← Hinzufügen!
  app.replicas: 5
```

### Fehler: `YAML-Datei ist leer`

**Ursache**: Die Werte-Datei ist leer oder enthält nur Whitespace.

**Lösung**:
1. Öffne die Datei
2. Füge Inhalt ein oder lösche die leere Datei
3. Versuche es erneut

### Fehler: `TypeError: main() got unexpected keyword argument`

**Ursache**: Das Skript wurde mit falschen Argumenten aufgerufen.

**Lösung**: Nutze nur das Skript wie in der Anleitung:

```bash
python3 scripts/cli_yaml_config_fill.py
```

### Fehler: Werte werden nicht korrekt ersetzt

**Ursache**: Die `transform`-Strategie passt nicht zu deinen Daten.

**Lösung**:

- Wenn deine Datei eine verschachtelte Struktur hat → verwende `fill_config_template`
- Wenn deine Datei Punkt-Notation hat (z. B. `app.replicas: 5`) → verwende `fill_simple_template`

---

## Tipps

1. **Basis-Template mit Defaults**  
   Füll das Basis-Template mit sensible Standardwerte (z. B. Ports, Ressourcen). Die Werte-Dateien überschreiben dann nur, was anders sein soll.

2. **Reihenfolge von `data_files` ist wichtig**  
   Später aufgeführte Werte-Dateien arbeiten auf dem bereits modifizierten Template.

3. **Backups prüfen**  
   Vor dem Erzeugen speichert das Skript die alte Datei als Backup (Suffix `_bak.yaml`). Schau dort nach, falls etwas schiefgeht.
   Beispiel: `deploy-wls-admin-dev_bak.yaml`

4. **Auf dem Server deployen**  
   Nutze die generierte Datei für dein Deployment:
   
   ```bash
   kubectl apply -f outpath/deploy-wls-admin-dev.yaml
   ```

---

## Weiterführende Ressourcen

Für **technische Details**, siehe:

- `docs/tutorial_cli_config_fill.md` – Vollständiges technisches Tutorial
- `yaml_config_support/config_models.py` – Datenstrukturen und Validierung
- `yaml_config_support/k8sValuesFill.py` – Kernlogik

---

## Fragen?

Bei Problemen:

1. Prüfe die **Fehlermeldung** oben in dieser Anleitung
2. Schaue in die `log/`-Datei (falls vorhanden)
3. Vergleiche deine `scripts/env.py` mit dem Muster oben
4. Lies das technische Tutorial, falls die einfache Anleitung nicht reicht

