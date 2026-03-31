import unittest
from collections import OrderedDict
from copy import deepcopy

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


if __name__ == "__main__":
    unittest.main()

