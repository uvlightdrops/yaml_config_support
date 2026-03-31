import os
import shutil
import sys
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from yaml_config_support.cli_config_fill import main
from yaml_config_support.config_models import FillOptions
from yaml_config_support.exceptions import MissingEnvironmentError
from yaml_config_support.k8sValuesFill import K8sValuesFill


class K8sValuesFillWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.keep_tempdirs = os.environ.get("KEEP_TEST_TEMPDIRS", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.base_dir = Path(tempfile.mkdtemp())
        self.template_dir = self.base_dir / "templates"
        self.secret_dir = self.base_dir / "secrets"
        self.out_dir = self.base_dir / "out"
        self.template_dir.mkdir()
        self.secret_dir.mkdir()

        self._write_yaml(
            self.template_dir / "values_onefitsall.yaml",
            {
                "service": {"port": 80},
                "secrets": {"username": "CHANGEME", "password": "CHANGEME"},
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
                "env": [{"name": "LOG_LEVEL", "value": "info"}],
            },
        )
        self._write_yaml(
            self.secret_dir / "values_creds_dev.yaml",
            {"secrets": {"username": "dev-user", "password": "dev-password"}},
        )
        self._write_yaml(
            self.secret_dir / "values_user.yaml",
            {"service": {"port": 8080}},
        )
        self._write_yaml(
            self.template_dir / "values_resources.yaml",
            {
                "dev": {
                    "resources.limits.cpu": "250m",
                    "lists": {"env": [{"name": "LOG_LEVEL", "value": "debug"}]},
                },
                "prod": {
                    "resources.limits.cpu": "500m",
                },
            },
        )

        self.options = {
            "default_template_dir": self.template_dir,
            "default_valuestore_dir": self.secret_dir,
            "outpath": self.out_dir,
            "data_files": OrderedDict(
                [
                    (
                        "creds",
                        {
                            "source": "private",
                            "transform": "fill_config_template",
                            "env": "yes",
                        },
                    ),
                    (
                        "resources",
                        {
                            "source": "project",
                            "transform": "fill_simple_template",
                            "env": "together",
                        },
                    ),
                    (
                        "user",
                        {
                            "source": "private",
                            "transform": "fill_config_template",
                            "env": "no",
                        },
                    ),
                ]
            ),
        }

        if self.keep_tempdirs:
            print(f"KEEP_TEST_TEMPDIRS aktiv, temporäres Testverzeichnis bleibt erhalten: {self.base_dir}")

    def tearDown(self):
        if self.keep_tempdirs:
            return
        shutil.rmtree(self.base_dir)

    def _write_yaml(self, path, payload):
        with path.open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(payload, file_handle, sort_keys=False)

    def test_k8s_values_fill_runs_end_to_end(self):
        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, self.options)

        result_path = fill.run(self.out_dir)

        with result_path.open("r", encoding="utf-8") as file_handle:
            result = yaml.safe_load(file_handle)
        self.assertEqual(result["service"]["port"], 8080)
        self.assertEqual(result["secrets"]["username"], "dev-user")
        self.assertEqual(result["resources"]["limits"]["cpu"], "250m")
        self.assertEqual(result["env"][0]["value"], "debug")

    def test_cli_main_accepts_custom_argv(self):
        result_path = main(
            self.options,
            [
                "dev",
                "--template_dir",
                str(self.template_dir),
                "--valuestore_dir",
                str(self.secret_dir),
                "--outdir",
                str(self.out_dir),
            ],
        )

        self.assertTrue(result_path.exists())
        self.assertEqual(result_path.name, "updated_values-dev.yaml")

    def test_missing_environment_in_together_file_raises_clear_error(self):
        self._write_yaml(
            self.secret_dir / "values_creds_qa.yaml",
            {"secrets": {"username": "qa-user", "password": "qa-password"}},
        )
        options = FillOptions.from_mapping(self.options)
        fill = K8sValuesFill("qa", self.template_dir, self.secret_dir, options)

        with self.assertRaises(MissingEnvironmentError):
            fill.load_files_spec()


if __name__ == "__main__":
    if "--keep-tempdirs" in sys.argv:
        os.environ["KEEP_TEST_TEMPDIRS"] = "1"
        sys.argv.remove("--keep-tempdirs")
    unittest.main()


