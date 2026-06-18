# Quick-Start: Cheat Sheet

Schnelle Referenz zum Ausführen des Skripts.

## 🚀 Basis-Befehl

```bash
cd /home/flow/dev_flow/yaml_config_support
python3 scripts/cli_yaml_config_fill.py
```

**Was passiert:**
- Liest `scripts/env.py`
- Lädt `template_dir/deploy-wls-admin.yaml`
- Lädt Werte-Dateien (definiert in `data_files`)
- Generiert Ausgabe unter `outpath/cf-{target_env}/`

---

## 📝 Konfiguration vor dem Ausführen anpassen

Öffne `scripts/env.py`:

```python
target_env = "dev"                 # Umgebung wechseln
valuestore_dir = "/pfad/zur/secrets"  # Pfad ändern
template_dir = "/pfad/zu/templates"   # Pfad ändern
```

---

## 🔄 Unterschiedliche Umgebungen

**Für Dev:**
```python
target_env = "dev"
```

**Für Prod:**
```python
target_env = "prod"
```

---

## 📂 Dateien, die du brauchen:

| Datei | Ort | Zweck |
|-------|-----|-------|
| `deploy-wls-admin.yaml` | `template_dir/` | Basis-Template |
| `values_resources.yaml` | `valuestore_dir/` | Werte für diese Umgebung |
| `scripts/env.py` | `scripts/` | Konfiguration |
| `scripts/cli_yaml_config_fill.py` | `scripts/` | Das Skript selbst |

---

## ✅ Ergebnis prüfen

Nach dem Ausführen schau dir die generierte Datei an:

```bash
cat /path/to/outpath/deploy-wls-admin-dev.yaml
```

---

## ⚠️ Häufige Fehler (Schnellfix)

| Fehler | Ursache | Fix |
|--------|---------|-----|
| `FileNotFoundError` | Werte-Datei nicht gefunden | Pfade in `env.py` prüfen |
| `MissingEnvironmentError` | Umgebungs-Block fehlt | In Werte-Datei `dev:` oder `prod:` Block hinzufügen |
| Werte werden nicht ersetzt | Falsche `transform` Strategie | Prüfe `fill_config_template` vs. `fill_simple_template` |
| Keine Ausgabedatei | Ausgabeverzeichnis falsch | `outpath` in `env.py` prüfen |

---

## 💾 Backup

Vor dem Überschreiben wird ein Backup erstellt:
```
outpath/<template-name>-<env>_bak.yaml
```

Beispiel: `deploy-wls-admin-dev_bak.yaml`

---

## 📖 Mehr Infos

- **Für Anfänger:** Siehe `README.md`
- **Für Techniker:** Siehe `TECHNICAL_TUTORIAL.md`

