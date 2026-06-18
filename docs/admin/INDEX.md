# 📚 Admin-Dokumentation: Überblick

Willkommen! Diese Dokumentation hilft dir, **YAML-Templates automatisch zu füllen** – für verschiedene Umgebungen (dev, prod, staging, etc.) ohne manuelle Bearbeitung.

---

## 📖 Dokumentation nach Verwendungsfall

Wähle je nach deiner Erfahrung:

### 🟢 **Anfänger? Starte hier:**

| Datei | Inhalt | Zeit |
|-------|--------|------|
| **[README.md](README.md)** | Komplette Anleitung von Grund auf | 15 Min |
| **[CHEAT_SHEET.md](CHEAT_SHEET.md)** | Schnelle Referenz zum Nachschlagen | 5 Min |
| **[EXAMPLE_PROJECT.md](EXAMPLE_PROJECT.md)** | Aufbau eines funktionierenden Beispiels | 10 Min |

### 🔵 **Erfahren? Schneller Überblick:**

| Datei | Inhalt |
|-------|--------|
| **[CHEAT_SHEET.md](CHEAT_SHEET.md)** | Alle wichtigen Befehle & Fehler |
| **[TECHNICAL_TUTORIAL.md](TECHNICAL_TUTORIAL.md)** | Tiefes technisches Verständnis |

### 🟣 **Für Python-Entwickler:**

| Datei | Inhalt |
|-------|--------|
| **[TECHNICAL_TUTORIAL.md](TECHNICAL_TUTORIAL.md)** | Direkte Python-Nutzung, Klassen, APIs |
| Quellcode | `yaml_config_support/k8sValuesFill.py` |

---

## 🎯 Häufigste Aufgaben (schnelle Links)

- **"Ich will einfach mal ein Beispiel sehen"** → [EXAMPLE_PROJECT.md](EXAMPLE_PROJECT.md)
- **"Ich brauche den genauen Befehl"** → [CHEAT_SHEET.md](CHEAT_SHEET.md)
- **"Ich bekomme einen Fehler"** → [README.md#fehlerbehebung](README.md#❌-fehlerbehebung)
- **"Ich verstehe nicht, wie die Werte-Dateien funktionieren"** → [README.md#dateistruktur-verstehen](README.md#📋-dateistruktur-verstehen)
- **"Ich brauche mehrere Templates"** → [README.md#task-2-eine-neue-werte-datei-hinzufügen](README.md#task-2-eine-neue-werte-datei-hinzufügen)
- **"Warum funktioniert es nicht?"** → [README.md#fehlerbehebung](README.md#❌-fehlerbehebung)

---

## 🚀 Die Grundidee in 30 Sekunden

```
┌─────────────────────────────────────────────────────────────┐
│  AUSGANGSLAGE:                                              │
│  • deploy-wls-admin.yaml (öffentliches Template)           │
│  • values_resources_dev.yaml (private Dev-Werte)           │
│  • values_resources_prod.yaml (private Prod-Werte)         │
└──────────────────────────────────────────────────────────────┘
                            ↓
                    (Dieses Skript)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  ERGEBNIS:                                                  │
│  • deploy-wls-admin-dev.yaml (für Kubectl Deploy)          │
│  • deploy-wls-admin-prod.yaml (für Kubectl Deploy)         │
└─────────────────────────────────────────────────────────────┘
```

Das Skript **kombiniert** das öffentliche Template mit deinen privaten Werten und erzeugt eine finale, einsatzbereite YAML-Datei.

Der Ausgabedateiname wird vom Template-Namen abgeleitet (z.B. `deploy-wls-admin.yaml` → `deploy-wls-admin-dev.yaml`).

---

## 📁 Verzeichnisstruktur

```
docs/admin/
├── README.md                    ← START HIER (für Anfänger)
├── CHEAT_SHEET.md              ← Schnelle Befehle & Fehler
├── EXAMPLE_PROJECT.md          ← Praktisches Beispiel zum Nachbauen
├── TECHNICAL_TUTORIAL.md       ← Für Techniker & Python-Nutzer
└── INDEX.md                    ← Diese Datei
```

---

## 🔄 Workflow

```
1. scripts/env.py bearbeiten      (Pfade & Umgebung setzen)
     ↓
2. Werte-Dateien erstellen        (dev, prod, secrets, etc.)
     ↓
3. python3 cli_yaml_config_fill.py   (Skript ausführen)
     ↓
4. Ergebnis prüfen                (<template>-<env>.yaml)
     ↓
5. kubectl apply                  (Deployen)
```

---

## ✅ Checkliste zum Starten

- [ ] `scripts/env.py` mit deinen Pfaden angepasst?
- [ ] `template_dir` existiert und enthält `deploy-wls-admin.yaml`?
- [ ] `valuestore_dir` existiert und enthält Werte-Dateien?
- [ ] `outpath` existiert (wird ggf. erstellt)?
- [ ] `target_env` auf deine Umgebung gesetzt?

---

## ⚡ Schnell-Befehl

```bash
cd /home/flow/dev_flow/yaml_config_support
python3 scripts/cli_yaml_config_fill.py
```

**Fertig!** Die Datei ist unter `outpath/<template-name>-<env>.yaml`.

Beispiel: `outpath/deploy-wls-admin-dev.yaml`

---

## 💬 Fragen?

1. **Anleitung nicht klar?** → Lies [README.md](README.md)
2. **Befehl nicht erinnert?** → Schau [CHEAT_SHEET.md](CHEAT_SHEET.md)
3. **Fehler bekommen?** → Geh zu [README.md#fehlerbehebung](README.md#❌-fehlerbehebung)
4. **Beispiel brauchen?** → [EXAMPLE_PROJECT.md](EXAMPLE_PROJECT.md)

---

**Version:** 1.0  
**Zuletzt aktualisiert:** 2025  
**Zielgruppe:** Administratoren und DevOps-Team

