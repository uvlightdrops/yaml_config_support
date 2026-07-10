# Validierung – env.yaml/env.yml Schema-Prüfung

## Überblick

`env_validator.py` validiert Projektkonfigurationen gegen ein striktes Schema. Fehler werden **früh erkannt** mit klaren, aussagekräftigen Meldungen — bevor irrelevante Befüllungsläufe stattfinden.

---

## Verwendung

### 1. CLI-Validierung (Standalone)

```bash
# Prüfe env.yaml vor dem Lauf
python3 -m yaml_config_support.env_validator path/to/env.yaml

# Exit-Code: 0 (OK), 1 (Fehler)
```

### 2. Integriert in cli_yaml_config_fill

Der Wrapper ruft `validate_env_config()` automatisch auf:

```bash
python3 scripts/cli_yaml_config_fill.py dev --overlay manual
# → env.yaml wird automatisch validiert
# → Fehler stoppen sofort mit Meldung
```

---

## Schema

### Erforderliche Top-Level Keys

| Key | Typ | Beschreibung |
|---|---|---|
| `basedir` | str | Projekt-Wurzelverzeichnis |
| `template_dir` | str | Verzeichnis mit Base-Templates |
| `valuestore_dir` | str | Verzeichnis mit Value-Overlays |
| `outpath` | str | Output-Verzeichnis für gefüllte Dateien |
| `data_files` | dict | Mapping der Befüll-Reihenfolge |

### Optionale Top-Level Keys

| Key | Typ | Standard | Beschreibung |
|---|---|---|---|
| `target_env` | str | `"dev"` | Default-Umgebung |
| `template_collect_dir` | str\|None | None | Auto-sammeln aus Verzeichnis |
| `template_files` | list | `[]` | Explizite Template-Dateien |
| `template_defaults` | dict | (s.u.) | Defaults für data_files-Einträge |
| `data_file_defaults` | dict | `{}` | Defaults für alle Specs |

### data_files Einträge

```yaml
data_files:
  <KEY>:                           # Eindeutige ID
    source: <"private"|"project">  # Erforderlich
    transform: <"fill_config_template"|"fill_simple_template">  # Erforderlich
    env: <"yes"|"no"|"together"|"fallback">                     # Erforderlich
    file: <custom_filename>        # Optional (nicht bei env='fallback')
    targets: ["deploy-*.yaml"]     # Optional (Standard: ["*"])
```

**Details:**

- **`source`**: Verzeichnis unter `valuestore_dir` (`private`, `project`)
- **`transform`**: Merge-Strategie (`fill_config_template` = deep merge, `fill_simple_template` = Pfad-basiert)
- **`env`**: Umgebungsvarianzbehandlung:
  - `"yes"`: Datei enthält `{env}` Platzhalter (z.B. `values_creds_dev.yaml`)
  - `"no"`: Datei hat keinen Env-Suffix (z.B. `values_user.yaml`)
  - `"together"`: Datei enthält Env-Keys im YAML (z.B. `dev: { ... }`)
  - `"fallback"`: Zuerst `_<env>`, sonst allgemeine Version
- **`file`**: Expliziter Dateiname; nur bei `env="yes"`, `"no"`, `"together"` erlaubt
- **`targets`**: Glob-Pattern für Template-Zuordnung (Standard: alle)

---

## Validierungsprüfungen

### Top-Level

✓ Alle erforderlichen Keys vorhanden  
✓ Typen korrekt (str, dict, list)  
✓ `template_collect_dir` ist str oder None  
✓ `template_files` ist list oder tuple  
✓ `template_defaults`, `data_file_defaults` sind dict  

### data_files

✓ `data_files` ist dict  
✓ `data_files` nicht leer  
✓ Jeder Eintrag ist dict  

### data_files Einträge

✓ `source` ist `"private"` oder `"project"`  
✓ `transform` ist `"fill_config_template"` oder `"fill_simple_template"`  
✓ `env` ist `"yes"`, `"no"`, `"together"` oder `"fallback"`  
✓ `env` akzeptiert auch YAML-Bool (`true` → `"yes"`, `false` → `"no"`)  
✓ `file` ist str; nicht erlaubt bei `env="fallback"`  
✓ `targets` ist list oder tuple; nicht leer; alle Elemente strings  

---

## Fehlerbeispiele

### Fehler: Ungültige `source`

```
✗ Validierungsfehler: env.yaml.data_files['creds'].source: Ungültig,
  muss einer dieser Werte sein: private, project. Erhalten: 'invalid'
```

**Behebung:** `source` auf `"private"` oder `"project"` setzen.

---

### Fehler: Fehlender erforderlicher Key

```
✗ Validierungsfehler: env.yaml: Erforderliche Top-Level-Keys fehlen: outpath
```

**Behebung:** `outpath` in der Konfiguration hinzufügen.

---

### Fehler: Leere data_files

```
✗ Validierungsfehler: env.yaml.data_files: Darf nicht leer sein
```

**Behebung:** Mindestens einen Eintrag in `data_files` hinzufügen.

---

### Fehler: file mit env=fallback

```
✗ Validierungsfehler: env.yaml.data_files['creds']:
  'file' wird bei env='fallback' nicht unterstützt
```

**Behebung:** Entweder `env` ändern oder `file` entfernen.

---

### Fehler: Leere targets

```
✗ Validierungsfehler: env.yaml.data_files['creds'].targets: Darf nicht leer sein
```

**Behebung:** `targets` entfernen (nutzt Standard `["*"]`) oder Glob-Pattern hinzufügen.

---

## Best Practices

1. **Frühe Validierung**: Vor Produktion oder CI/CD läuft Validierung automatisch
2. **Klare Fehlermeldungen**: Zeigt Pfad, erwartete Werte, erhaltene Werte
3. **YAML-Bool-Normalisierung**: `env: true` wird zu `"yes"` normalisiert (flexibel)
4. **Tests**: 11 Validierungstests decken normale und Edge-Cases ab

---

## Tests

```bash
# Nur Validierungstests
python3 -m unittest tests.test_env_validator -v

# Alle Tests
python3 -m unittest discover -s tests -v
```

---

## Erweiterung

Um neue Validierungsregeln hinzuzufügen, bearbeite `validate_env_config()` in `env_validator.py`:

```python
# Beispiel: Neue Validierung für `outpath`
outpath = config.get("outpath")
if outpath and not Path(outpath).exists():
    raise EnvConfigValidationError(f"outpath existiert nicht: {outpath}")
```

Dann füge einen entsprechenden Test in `test_env_validator.py` hinzu.

