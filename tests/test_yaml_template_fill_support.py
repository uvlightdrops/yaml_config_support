import unittest
from collections import OrderedDict
from copy import deepcopy

from yaml_config_support.exceptions import PathNotFoundError
from yaml_config_support.yamlTemplateFillSupport import YamlTemplateFillSupport


class YamlTemplateFillSupportTests(unittest.TestCase):
    def setUp(self):
        self.fill_support = YamlTemplateFillSupport()

    def test_fill_config_template_keeps_defaults_and_overwrites_matching_keys(self):
        template = OrderedDict(
            {
                "service": {"port": 80, "host": "default.local"},
                "image": {"tag": "latest"},
            }
        )
        values = {"service": {"port": 8080}}

        result = self.fill_support.fill_config_template(template, values)

        self.assertEqual(result["service"]["port"], 8080)
        self.assertEqual(result["service"]["host"], "default.local")
        self.assertEqual(result["image"]["tag"], "latest")

    def test_fill_simple_template_updates_paths_and_does_not_mutate_values_input(self):
        template = {
            "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            "env": [{"name": "LOG_LEVEL", "value": "info"}],
        }
        values = {
            "resources.limits.cpu": "250m",
            "lists": {"env": [{"name": "LOG_LEVEL", "value": "debug"}]},
        }
        original_values = deepcopy(values)

        result = self.fill_support.fill_simple_template(template, values)

        self.assertEqual(result["resources"]["limits"]["cpu"], "250m")
        self.assertEqual(result["env"][0]["value"], "debug")
        self.assertEqual(values, original_values)

    def test_fill_simple_template_replaces_primitive_lists(self):
        template = {"hosts": ["a.example", "b.example"]}
        values = {"lists": {"hosts": ["x.example", "y.example"]}}

        result = self.fill_support.fill_simple_template(template, values)

        self.assertEqual(result["hosts"], ["x.example", "y.example"])

    def test_fill_simple_template_sets_list_index_notation(self):
        """containers[0].image setzt korrekt den ersten Container-Eintrag."""
        template = {
            "spec": {
                "containers": [
                    {"name": "app", "image": "latest"},
                    {"name": "sidecar", "image": "sidecar:latest"},
                ]
            }
        }
        values = {"spec.containers[0].image": "registry/app:dev"}

        result = self.fill_support.fill_simple_template(template, values)

        self.assertEqual(result["spec"]["containers"][0]["image"], "registry/app:dev")
        self.assertEqual(result["spec"]["containers"][1]["image"], "sidecar:latest")

    def test_fill_simple_template_deep_k8s_path_with_list_index(self):
        """Tiefer Kubernetes-Pfad mit containers[0] wird vollständig aufgelöst."""
        template = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {"name": "wls", "image": "weblogic:latest", "resources": {"limits": {"cpu": "100m"}}}
                        ]
                    }
                }
            }
        }
        values = {
            "spec.template.spec.containers[0].image": "registry/wls:dev",
            "spec.template.spec.containers[0].resources.limits.cpu": "500m",
        }

        result = self.fill_support.fill_simple_template(template, values)

        self.assertEqual(result["spec"]["template"]["spec"]["containers"][0]["image"], "registry/wls:dev")
        self.assertEqual(result["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"], "500m")

    def test_fill_simple_template_raises_path_not_found_for_missing_key(self):
        """Ein Pfad zu einem nicht vorhandenen Schlüssel wirft PathNotFoundError."""
        template = {"image": "latest"}
        values = {"resources.limits.cpu": "200m"}

        with self.assertRaises(PathNotFoundError):
            self.fill_support.fill_simple_template(template, values)


if __name__ == "__main__":
    unittest.main()

