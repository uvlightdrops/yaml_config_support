# Tutorial: YAML-Templates mit getrennten Wertedateien füllen

Dieses Tutorial zeigt den praktischen Einsatz von:

- `yaml_config_support/cli_config_fill.py`
- `yaml_config_support/k8sValuesFill.py`
- `yaml_config_support/yamlTemplateFillSupport.py`
- `scripts/cli_yaml_config_fill.py`

Ziel ist eine Arbeitsweise, bei der:

- das allgemeine YAML-Template im Projekt liegt,
- sensible Werte separat im Value-Store liegen,
- mehrere Umgebungen unterstützt werden,
- am Ende eine finale Kubernetes-Values-Datei erzeugt wird.

---

## 1. Grundidee

Der Ablauf besteht aus vier Schritten:

1. Das Basis-Template `values_onefitsall.yaml` laden.
2. Weitere Wertedateien entsprechend `data_files` laden.
3. Jede dieser Dateien mit der angegebenen Transformationsstrategie anwenden.
4. Das Resultat als finale YAML-Datei speichern.

Das ist besonders praktisch für Helm- oder andere Deployment-Values, wenn öffentliche Defaults und sensible Daten getrennt bleiben sollen.

---

## 2. Die beteiligten Dateien

### `yaml_config_support/cli_config_fill.py`

Das Modul stellt die Funktion `main(options)` bereit.  
Sie liest die CLI-Argumente und startet dann intern `K8sValuesFill`.

### `yaml_config_support/k8sValuesFill.py`

Diese Klasse übernimmt den eigentlichen Workflow:

- Basis-Template laden
- Overlay-Dateien laden
- Transformationen anwenden
- Ausgabedatei schreiben

### `yaml_config_support/yamlTemplateFillSupport.py`

Hier sind die zwei Template-Strategien implementiert:

#### `fill_config_template(template_d, values_d)`

Diese Strategie erwartet verschachtelte Dicts.  
Sie überschreibt nur Werte, die im Template bereits angelegt sind.

Beispiel:

```yaml
# Template
app:
  host: default.local
  port: 80
```

```yaml
# Werte
app:
  port: 8080
```

Ergebnis:

```yaml
app:
  host: default.local
  port: 8080
```

#### `fill_simple_template(template_d, values_d)`

Diese Strategie arbeitet mit Punktpfaden:

```yaml
resources.limits.cpu: 200m
resources.limits.memory: 256Mi
```

Zusätzlich gibt es den Spezialschlüssel `lists`, um bestehende Listen zu aktualisieren oder zu ersetzen.

### `scripts/cli_yaml_config_fill.py`

Das ist ein Beispiel-Wrapper für ein konkretes Projekt.  
Dort definierst du die Standardpfade und die `data_files`-Konfiguration.

---

## 3. Bedeutung von `data_files`

`data_files` beschreibt, welche Dateien geladen werden und wie sie angewendet werden.

Beispiel:

```python
data_files = {
    'creds': {
        'source': 'private',
        'transform': 'fill_config_template',
        'env': 'yes',
    },
    'resources': {
        'source': 'project',
        'transform': 'fill_simple_template',
        'env': 'together',
    },
    'user': {
        'source': 'private',
        'transform': 'fill_config_template',
        'env': 'no',
    },
}
```

### `source`

- `private`  
  Datei wird aus `valuestore_dir` gelesen.
- `project`  
  Datei wird aus `template_dir` gelesen.

### `transform`

- `fill_config_template`  
  Rekursive Dict-Überlagerung.
- `fill_simple_template`  
  Punktpfade plus optionale Listenbearbeitung.

### `env`

- `yes`  
  Der Dateiname enthält die Umgebung, z. B. `values_creds_dev.yaml`.
- `no`  
  Der Dateiname ist für alle Umgebungen gleich, z. B. `values_user.yaml`.
- `together`  
  Die Datei enthält mehrere Umgebungen als Ober-Schlüssel, zum Beispiel `dev:` und `prod:`.

Wichtig: Die Reihenfolge der Einträge in `data_files` steuert die Reihenfolge der Overlays.

---

## 4. Erwartete Dateien und Namen

### Basis-Template

Immer erforderlich:

```text
<template_dir>/values_onefitsall.yaml
```

### Weitere Dateien

Für einen Schlüssel wie `creds` oder `resources` gilt:

- `env == "yes"`  → `values_<key>_<env>.yaml`
- `env == "no"`   → `values_<key>.yaml`
- `env == "together"` → `values_<key>.yaml`

Beispiele:

```text
values_creds_dev.yaml
values_user.yaml
values_resources.yaml
```

---

## 5. Vollständiges Minimalbeispiel

### Verzeichnisstruktur

```text
example/
├── templates/
│   ├── values_onefitsall.yaml
│   └── values_resources.yaml
└── secrets/
    ├── values_creds_dev.yaml
    └── values_user.yaml
```

### `templates/values_onefitsall.yaml`

```yaml
image:
  repository: demo/app
  tag: latest
service:
  port: 80
secrets:
  username: CHANGEME
  password: CHANGEME
resources:
  limits:
    cpu: 100m
    memory: 128Mi
env:
  - name: LOG_LEVEL
    value: info
```

### `secrets/values_creds_dev.yaml`

```yaml
secrets:
  username: dev-user
  password: dev-password
```

Diese Datei passt gut zu `fill_config_template`, weil ihre Struktur dem Template entspricht.

### `secrets/values_user.yaml`

```yaml
service:
  port: 8080
```

Auch das ist ein rekursives Overlay.

### `templates/values_resources.yaml`

```yaml
dev:
  resources.limits.cpu: 200m
  resources.limits.memory: 256Mi
  lists:
    env:
      - name: LOG_LEVEL
        value: debug
prod:
  resources.limits.cpu: 500m
  resources.limits.memory: 512Mi
  lists:
    env:
      - name: LOG_LEVEL
        value: warn
```

Diese Datei passt zu `fill_simple_template` und `env: together`.

---

## 6. Projekt-Wrapper schreiben

Ein Wrapper kapselt die projektbezogenen Standardpfade.  
In diesem Repository ist `scripts/cli_yaml_config_fill.py` genau so ein Wrapper.

Das Prinzip ist:

```python
from yaml_config_support.cli_config_fill import main

options = {
    'default_template_dir': '/pfad/zu/templates',
    'default_valuestore_dir': '/pfad/zu/secrets',
    'outpath': '/pfad/fuer/output',
    'data_files': data_files,
}

if __name__ == '__main__':
    main(options)
```

---

## 7. CLI benutzen

### Hilfe anzeigen

```bash
python scripts/cli_yaml_config_fill.py --help
```

### Für `dev` ausführen

```bash
python scripts/cli_yaml_config_fill.py dev
```

### Eigenes Ausgabeverzeichnis setzen

```bash
python scripts/cli_yaml_config_fill.py dev --outdir /tmp/result
```

### Template- und Value-Store-Verzeichnis überschreiben

```bash
python scripts/cli_yaml_config_fill.py dev \
  --template_dir /tmp/example/templates \
  --valuestore_dir /tmp/example/secrets \
  --outdir /tmp/example/out
```

Die Ergebnisdatei landet unter:

```text
<outdir>/cf-dev/updated_values-dev.yaml
```

Wenn die Datei bereits existiert, wird vorher eine Sicherung mit dem Suffix `_bak.yaml` angelegt.

---

## 8. Was genau machen die beiden Transformationsarten?

## A. `fill_config_template`

Verwendung:

- wenn deine Overlay-Datei dieselbe verschachtelte Struktur wie das Template hat
- gut für Secrets, Benutzerwerte oder klassische Konfig-Abschnitte

Eigenschaften:

- rekursiv
- überschreibt nur vorhandene Schlüssel im Template
- belässt Standardwerte, wenn kein Overlay-Wert existiert

## B. `fill_simple_template`

Verwendung:

- wenn du gezielt einzelne Pfade setzen willst
- gut für technische Werte wie Ressourcenlimits oder vereinzelte Overrides

Eigenschaften:

- nutzt Punktnotation wie `a.b.c`
- unterstützt `lists` für Listen im Template
- verändert das Template direkt

### Verhalten von `lists`

Es gibt zwei Modi:

1. **Primitive Liste ersetzen**

```yaml
lists:
  some.path:
    - one
    - two
```

Dann wird die bestehende Liste vollständig ersetzt.

2. **Liste aus Dictionaries aktualisieren**

Wenn im Template z. B. steht:

```yaml
env:
  - name: LOG_LEVEL
    value: info
```

und das Overlay enthält:

```yaml
lists:
  env:
    - name: LOG_LEVEL
      value: debug
```

wird der vorhandene Eintrag mit `name: LOG_LEVEL` gefunden und aktualisiert.

---

## 9. Ausgabe und Ergebnis

Nach dem Lauf schreibt `K8sValuesFill.write_output()` die finale Datei nach:

```text
<outdir>/cf-<env>/updated_values-<env>.yaml
```

Beispiel:

```text
/tmp/example/out/cf-dev/updated_values-dev.yaml
```

---

## 10. Praktische Hinweise

### Reihenfolge der Overlays beachten

Die Reihenfolge in `data_files` ist wichtig.  
Spätere Overlays arbeiten auf dem bereits veränderten Template weiter.

### Templates sollten die Zielstruktur schon enthalten

Besonders `fill_config_template` funktioniert am besten, wenn das Grund-Template die gewünschte Struktur bereits vorgibt.

### `env: together` ist für Umgebungsblöcke praktisch

Damit kannst du eine einzige Projektdatei wie `values_resources.yaml` führen und darin `dev`, `test`, `prod` als Ober-Schlüssel verwalten.

### Aktueller Stand der CLI-Argumente

Die Argumente `--ypath_keys` und `--ydict_keys` sind in der CLI vorhanden, werden aber im aktuellen Code noch nicht weiter benutzt.

---

## 11. Direkte Nutzung aus Python

Wenn du nicht über den Wrapper gehen willst, kannst du die Klasse direkt verwenden:

```python
from yaml_config_support.k8sValuesFill import K8sValuesFill

options = {
    'verbose': True,
    'data_files': {
        'creds': {
            'source': 'private',
            'transform': 'fill_config_template',
            'env': 'yes',
        },
        'resources': {
            'source': 'project',
            'transform': 'fill_simple_template',
            'env': 'together',
        },
        'user': {
            'source': 'private',
            'transform': 'fill_config_template',
            'env': 'no',
        },
    },
}

fill = K8sValuesFill(
    env='dev',
    template_dir='/tmp/example/templates',
    creds_dir='/tmp/example/secrets',
    options=options,
)
fill.load_files()
fill.fill_configs()
fill.write_output('/tmp/example/out', 'dev')
```

Das ist hilfreich für Tests oder für eine Integration in andere Python-Skripte.

---

## 12. Zusammenfassung

Wenn du das System nutzen willst, brauchst du im Kern nur:

1. ein `values_onefitsall.yaml`,
2. eine `data_files`-Beschreibung,
3. getrennte Projekt- und Secret-Dateien,
4. einen Wrapper, der `main(options)` aufruft.

Damit kannst du reproduzierbar aus einem allgemeinen YAML-Template umgebungsabhängige und sensible Konfigurationen zusammenführen.

