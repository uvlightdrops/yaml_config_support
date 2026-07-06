"""
Beispiel-Konfiguration für ansible_mk Projekt
mit weblogic Deployments.

Kopiere diese Datei zu: env.py und passe die Pfade an.
"""

from collections import OrderedDict
from pathlib import Path

# ============================================================================
# Basisverzeichnisse – Anpassung erforderlich!
# ============================================================================

home_dir = Path.home()
project_base = home_dir / "dev_mk" / "ansible_mk"

# Zielumgebung (dev, test, prod)
target_env = "dev"

# Template-Quelle (git-kontrolliert)
template_dir = project_base / "k8s"

# Overlay-Verzeichnis (wird per template_collect_dir auto-collected)
template_collect_dir = project_base / "k8s" / "overlays" / "manual"

# Werte-Speicher (gitignored, enthält Credentials)
valuestore_dir = project_base / "private"

# Ausgabe-Verzeichnis (wird erzeugt, enthält gefüllte YAMLs)
outpath = project_base / "ready2apply"

basedir = project_base


# ============================================================================
# Template-Konfiguration
# ============================================================================

# Alte Art (explizit auflisten) – wird nicht verwendet wenn template_collect_dir gesetzt
template_files = []

# Template-Defaults für neue Datein
template_defaults = {
    "source": "project",
    "transform": "fill_config_template",
}


# ============================================================================
# Data Files – Overlays laden und mergen
# ============================================================================

data_file_defaults = {
    "source": "project",
    "transform": "fill_simple_template",
    "env": "together",  # oder "yes", "no", "fallback"
}

# Reihenfolge ist wichtig! Später einträge überschreiben frühere.
data_files = OrderedDict(
    [
        (
            "resources",
            {
                "source": "project",
                "transform": "fill_simple_template",
                "env": "together",
            },
        ),
        (
            "creds",
            {
                "source": "private",
                "transform": "fill_config_template",
                "env": "yes",  # values_creds_dev.yaml, values_creds_prod.yaml
            },
        ),
    ]
)

