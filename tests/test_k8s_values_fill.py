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
from yaml_config_support.exceptions import DataFileConfigurationError, EmptyYamlFileError, MissingEnvironmentError
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
            "data_file_defaults": {
                "source": "project",
                "transform": "fill_simple_template",
                "env": "together",
            },
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
                    ("resources", {}),
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
        self.assertEqual(result_path.name, "values_onefitsall-dev.yaml")

    def test_missing_environment_in_together_file_raises_clear_error(self):
        self._write_yaml(
            self.secret_dir / "values_creds_qa.yaml",
            {"secrets": {"username": "qa-user", "password": "qa-password"}},
        )
        options = FillOptions.from_mapping(self.options)
        fill = K8sValuesFill("qa", self.template_dir, self.secret_dir, options)

        with self.assertRaises(MissingEnvironmentError):
            fill.load_files_spec()

    def test_empty_yaml_file_raises_clear_error(self):
        (self.secret_dir / "values_user.yaml").write_text("", encoding="utf-8")
        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, self.options)

        with self.assertRaises(EmptyYamlFileError):
            fill.load_files_spec()

    def test_multiple_template_files_apply_data_to_each_template(self):
        self._write_yaml(
            self.template_dir / "deploy-a.yaml",
            {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [{"name": "wls-admin", "image": "old:image"}],
                        }
                    }
                }
            },
        )
        self._write_yaml(
            self.template_dir / "deploy-b.yaml",
            {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [{"name": "wls-managed", "image": "old:image"}],
                        }
                    }
                }
            },
        )

        options = {
            "default_template_dir": self.template_dir,
            "default_valuestore_dir": self.secret_dir,
            "outpath": self.out_dir,
            "template_defaults": {
                "source": "project",
                "transform": "fill_config_template",
            },
            "template_files": ["deploy-a.yaml", "deploy-b.yaml"],
            "data_file_defaults": {
                "source": "project",
                "transform": "fill_simple_template",
                "env": "no",
            },
            "data_files": OrderedDict(
                [
                    (
                        "resources",
                        {
                            "source": "project",
                            "transform": "fill_simple_template",
                            "env": "no",
                        },
                    )
                ]
            ),
        }
        self._write_yaml(
            self.template_dir / "values_resources.yaml",
            {"spec.template.spec.containers[0].image": "new:image"},
        )

        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        result_paths = fill.run(self.out_dir)

        self.assertEqual(len(result_paths), 2)
        result_a = self.out_dir / "deploy-a-dev.yaml"
        result_b = self.out_dir / "deploy-b-dev.yaml"
        self.assertTrue(result_a.exists())
        self.assertTrue(result_b.exists())

        with result_a.open("r", encoding="utf-8") as file_handle:
            data_a = yaml.safe_load(file_handle)
        with result_b.open("r", encoding="utf-8") as file_handle:
            data_b = yaml.safe_load(file_handle)

        self.assertEqual(data_a["spec"]["template"]["spec"]["containers"][0]["image"], "new:image")
        self.assertEqual(data_b["spec"]["template"]["spec"]["containers"][0]["image"], "new:image")

    def test_fill_options_applies_data_file_defaults_and_overrides(self):
        options = FillOptions.from_mapping(self.options)
        self.assertEqual(options.data_files["resources"].transform, "fill_simple_template")
        self.assertEqual(options.data_files["resources"].source, "project")
        self.assertEqual(options.data_files["resources"].env, "together")
        self.assertEqual(options.data_files["resources"].targets, ("*",))
        self.assertEqual(options.data_files["creds"].source, "private")
        self.assertEqual(options.data_files["creds"].transform, "fill_config_template")
        self.assertEqual(options.template_files[0].path, "values_onefitsall.yaml")

    def test_data_file_targets_apply_only_to_matching_templates(self):
        self._write_yaml(
            self.template_dir / "deploy-a.yaml",
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [{"name": "app", "image": "old:image"}],
                        }
                    }
                },
            },
        )
        self._write_yaml(
            self.template_dir / "kustomization.yaml",
            {
                "apiVersion": "kustomize.config.k8s.io/v1beta1",
                "kind": "Kustomization",
                "resources": ["deploy-a.yaml"],
            },
        )
        self._write_yaml(
            self.secret_dir / "values_harbour_dev.yaml",
            {"spec.template.spec.containers[0].image": "new:image"},
        )

        options = {
            "default_template_dir": self.template_dir,
            "default_valuestore_dir": self.secret_dir,
            "outpath": self.out_dir,
            "template_files": ["deploy-a.yaml", "kustomization.yaml"],
            "data_files": OrderedDict(
                [
                    (
                        "harbour",
                        {
                            "source": "private",
                            "transform": "fill_simple_template",
                            "env": "yes",
                            "targets": ["deploy-*.yaml"],
                        },
                    )
                ]
            ),
        }

        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        result_paths = fill.run(self.out_dir)
        self.assertEqual(len(result_paths), 2)

        with (self.out_dir / "deploy-a-dev.yaml").open("r", encoding="utf-8") as file_handle:
            deploy_data = yaml.safe_load(file_handle)
        with (self.out_dir / "kustomization-dev.yaml").open("r", encoding="utf-8") as file_handle:
            kustomization_data = yaml.safe_load(file_handle)

        self.assertEqual(deploy_data["spec"]["template"]["spec"]["containers"][0]["image"], "new:image")
        self.assertEqual(kustomization_data["kind"], "Kustomization")
        self.assertEqual(kustomization_data["resources"], ["deploy-a.yaml"])

    def test_data_file_custom_file_name_with_env_placeholder(self):
        self._write_yaml(
            self.secret_dir / "registry-dev.yaml",
            {"service": {"port": 9090}},
        )
        options = {
            "default_template_dir": self.template_dir,
            "default_valuestore_dir": self.secret_dir,
            "outpath": self.out_dir,
            "data_files": OrderedDict(
                [
                    (
                        "registry",
                        {
                            "source": "private",
                            "transform": "fill_config_template",
                            "env": "yes",
                            "file": "registry-{env}.yaml",
                        },
                    )
                ]
            ),
        }

        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        result_path = fill.run(self.out_dir)
        with result_path.open("r", encoding="utf-8") as file_handle:
            result = yaml.safe_load(file_handle)
        self.assertEqual(result["service"]["port"], 9090)

    def test_data_file_custom_file_is_invalid_for_fallback(self):
        options = dict(self.options)
        options["data_files"] = OrderedDict(
            [
                (
                    "resources",
                    {
                        "source": "project",
                        "transform": "fill_simple_template",
                        "env": "fallback",
                        "file": "values_resources.yaml",
                    },
                )
            ]
        )

        with self.assertRaises(DataFileConfigurationError):
            FillOptions.from_mapping(options)

    def test_env_mode_normalizes_yaml_bool_values(self):
        options = dict(self.options)
        options["data_files"] = OrderedDict(
            [
                (
                    "creds",
                    {
                        "source": "private",
                        "transform": "fill_config_template",
                        "env": True,
                    },
                ),
                (
                    "user",
                    {
                        "source": "private",
                        "transform": "fill_config_template",
                        "env": False,
                    },
                ),
            ]
        )
        normalized = FillOptions.from_mapping(options)
        self.assertEqual(normalized.data_files["creds"].env, "yes")
        self.assertEqual(normalized.data_files["user"].env, "no")

    def test_concat_template_documents_writes_multi_doc_yaml(self):
        self._write_yaml(
            self.template_dir / "deploy-a.yaml",
            {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "a"}},
        )
        self._write_yaml(
            self.template_dir / "deploy-b.yaml",
            {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "b"}},
        )

        options = {
            "default_template_dir": self.template_dir,
            "default_valuestore_dir": self.secret_dir,
            "outpath": self.out_dir,
            "template_defaults": {
                "source": "project",
                "transform": "concat_template_documents",
            },
            "template_files": ["deploy-a.yaml", "deploy-b.yaml"],
            "data_files": OrderedDict(),
        }

        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        result_path = fill.run(self.out_dir)

        with result_path.open("r", encoding="utf-8") as file_handle:
            docs = list(yaml.safe_load_all(file_handle))
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0]["metadata"]["name"], "a")
        self.assertEqual(docs[1]["metadata"]["name"], "b")

    def test_fallback_env_uses_specific_file_when_present(self):
        """Bei env='fallback': nimmt values_resources_dev.yaml wenn vorhanden."""
        self._write_yaml(
            self.template_dir / "values_resources_dev.yaml",
            {"resources.limits.cpu": "999m"},
        )
        options = dict(self.options)
        options["data_file_defaults"] = {
            "source": "project",
            "transform": "fill_simple_template",
            "env": "fallback",
        }
        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        fill.load_files()
        self.assertEqual(fill.data["resources"]["resources.limits.cpu"], "999m")

    def test_fallback_env_uses_general_file_when_no_specific(self):
        """Bei env='fallback': fällt auf values_resources.yaml zurück wenn keine spez. Datei."""
        # values_resources_dev.yaml existiert NICHT, aber values_resources.yaml
        # (die "together"-Variante aus setUp) wird als general-Datei verwendet,
        # jedoch OHNE Env-Extraktion – direkt von oben gelesen
        self._write_yaml(
            self.template_dir / "values_resources.yaml",
            {"resources.limits.cpu": "fallback-value"},
        )
        options = dict(self.options)
        options["data_file_defaults"] = {
            "source": "project",
            "transform": "fill_simple_template",
            "env": "fallback",
        }
        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        fill.load_files()
        self.assertEqual(fill.data["resources"]["resources.limits.cpu"], "fallback-value")

    def test_fallback_env_raises_when_neither_file_exists(self):
        """Bei env='fallback': YamlFileAccessError wenn weder spez. noch allg. Datei vorhanden."""
        from yaml_config_support.exceptions import YamlFileAccessError
        (self.template_dir / "values_resources.yaml").unlink()
        options = dict(self.options)
        options["data_file_defaults"] = {
            "source": "project",
            "transform": "fill_simple_template",
            "env": "fallback",
        }
        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        with self.assertRaises(YamlFileAccessError):
            fill.load_files_spec()

    def test_template_collect_dir_loads_all_yaml_files(self):
        """template_collect_dir sammelt automatisch alle *.yaml Dateien aus einem Verzeichnis."""
        # Erstelle ein Overlay-Verzeichnis mit mehreren YAMLs
        overlay_dir = self.base_dir / "overlays" / "manual"
        overlay_dir.mkdir(parents=True)
        self._write_yaml(
            overlay_dir / "deployment.yaml",
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "app"},
            },
        )
        self._write_yaml(
            overlay_dir / "service.yaml",
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": "app-svc"},
            },
        )
        
        # Options mit template_collect_dir
        options = dict(self.options)
        options["template_collect_dir"] = str(overlay_dir)
        options["data_files"] = OrderedDict([
            (
                "creds",
                {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": "yes",
                },
            ),
        ])
        
        fill = K8sValuesFill("dev", self.template_dir, self.secret_dir, options)
        fill.load_files()
        
        # Es sollten 2 Templates geladen sein (deployment.yaml, service.yaml)
        self.assertEqual(fill.template_mode, "per_template")
        self.assertEqual(len(fill.template), 2)
        self.assertEqual(fill.template[0]["kind"], "Deployment")
        self.assertEqual(fill.template[1]["kind"], "Service")


if __name__ == "__main__":
    if "--keep-tempdirs" in sys.argv:
        os.environ["KEEP_TEST_TEMPDIRS"] = "1"
        sys.argv.remove("--keep-tempdirs")
    unittest.main()
