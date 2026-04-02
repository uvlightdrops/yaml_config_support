from pathlib import Path

# Beispielwert, an das Zielprojekt anpassen.
project_subpath = "dev_ldbv"
home_dir = Path.home()
basedir = home_dir / project_subpath
template_dir = basedir / "codefy_data" / "helmchart"
valuestore_dir = basedir / "codefy_creds"
outpath = basedir / "cf"

