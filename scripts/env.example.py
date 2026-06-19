from collections import OrderedDict
from pathlib import Path

# Beispielwert, an das Zielprojekt anpassen.
home_dir = Path.home()
project_subpath = "dev_sub"
target_env = "dev"
basedir = home_dir / project_subpath / "k8s_weblogic"
template_dir = basedir / "k8s"
valuestore_dir = basedir
outpath = basedir / "out"
template_file_name = "deploy-wls-admin.yaml"

template_defaults = {
    "source": "project",
    "transform": "fill_config_template",
}
template_files = [
    "deploy-wls-admin.yaml",
    "deploy-wls-managed-1.yaml",
    "deploy-wls-managed-2.yaml",
    "deploy-wls-managed-3.yaml",
]

data_file_defaults = {
    "source": "project",
    "transform": "fill_simple_template",
    "env": "fallback",
}
data_files = OrderedDict(
    [
        (
            "resources",
            {
                "source": "project",
                "transform": "fill_simple_template",
                "env": "no",
            },
        ),
    ]
)

