"""Tests für env.yaml-Validierung."""

import unittest
from pathlib import Path
import tempfile
import shutil

from yaml_config_support.env_validator import validate_env_config, EnvConfigValidationError


class EnvValidatorTests(unittest.TestCase):
    def test_valid_minimal_config(self):
        """Minimale gültige Konfiguration wird akzeptiert."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": "yes",
                }
            },
        }
        validate_env_config(config, "test.yaml")

    def test_missing_required_top_level_key(self):
        """Fehlender erforderlicher Top-Level-Key wird erkannt."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            # valuestore_dir fehlt
            "outpath": "/tmp/out",
            "data_files": {},
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("valuestore_dir", str(ctx.exception))

    def test_invalid_source_value(self):
        """Ungültige `source`-Value wird erkannt."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "invalid_source",
                    "transform": "fill_config_template",
                    "env": "yes",
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("source", str(ctx.exception))
        self.assertIn("invalid_source", str(ctx.exception))

    def test_invalid_transform_value(self):
        """Ungültige `transform`-Value wird erkannt."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "invalid_transform",
                    "env": "yes",
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("transform", str(ctx.exception))

    def test_invalid_env_value(self):
        """Ungültige `env`-Value wird erkannt."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": "invalid_env",
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("env", str(ctx.exception))

    def test_bool_env_value_normalized(self):
        """YAML-Bool-Werte für `env` werden akzeptiert (normalisiert zu yes/no)."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": True,
                }
            },
        }
        validate_env_config(config, "test.yaml")

    def test_file_with_fallback_env_is_invalid(self):
        """Kombination `file` + `env: fallback` ist ungültig."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": "fallback",
                    "file": "values_creds.yaml",
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("fallback", str(ctx.exception))
        self.assertIn("file", str(ctx.exception))

    def test_empty_targets_is_invalid(self):
        """Leere `targets`-Liste ist ungültig."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": "yes",
                    "targets": [],
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("targets", str(ctx.exception))

    def test_non_string_targets_element(self):
        """Nicht-String Element in `targets` wird erkannt."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    "transform": "fill_config_template",
                    "env": "yes",
                    "targets": ["deploy-*.yaml", 123],
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("targets", str(ctx.exception))

    def test_empty_data_files_is_invalid(self):
        """Leere `data_files` ist ungültig."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {},
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("data_files", str(ctx.exception))
        self.assertIn("nicht leer", str(ctx.exception))

    def test_missing_data_file_required_key(self):
        """Fehlender erforderlicher Key in data_files-Eintrag wird erkannt."""
        config = {
            "basedir": "/tmp",
            "template_dir": "/tmp/k8s",
            "valuestore_dir": "/tmp/values",
            "outpath": "/tmp/out",
            "data_files": {
                "creds": {
                    "source": "private",
                    # transform fehlt
                    "env": "yes",
                }
            },
        }
        with self.assertRaises(EnvConfigValidationError) as ctx:
            validate_env_config(config, "test.yaml")
        self.assertIn("transform", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

