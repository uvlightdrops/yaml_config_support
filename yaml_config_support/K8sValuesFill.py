from yaml_config_support.yamlTemplateFillSupport import YamlTemplateFillSupport
import yaml


class K8sValuesFill(YamlTemplateFillSupport):
    def __init__(self, template_dir, creds_dir, env='dev', verbose=False):
        super().__init__(verbose=verbose)
        self.template_dir = template_dir
        self.creds_dir = creds_dir
        self.env = env

    def load_files(self):
        fn = '%s/values_%s.yaml' % (self.template_dir, 'onefitsall')
        self.out("TEMPLATE file: ", fn)
        with open(fn, 'r') as f:
            self.template = yaml.safe_load(f)
        fn = '%s/values_resources.yaml' % (self.template_dir)
        self.out("RESOURCES file: " + fn)
        with open(fn, 'r') as f:
            res_yaml = yaml.safe_load(f)
            self.resources = res_yaml[self.env]
        fn = '%s/values_creds_%s.yaml' % (self.creds_dir, self.env)
        self.out("CREDS file:    ", fn)
        with open(fn, 'r') as f:
            self.creds = yaml.safe_load(f)
        fn = '%s/values_user.yaml' % (self.creds_dir)
        self.out("USER file:     ", fn)
        with open(fn, 'r') as f:
            self.user = yaml.safe_load(f)

    def test_config_fill(self, out_fp):
        result = self.fill_config_template(self.template, self.creds)
        result2 = self.fill_config_template(result, self.user)
        result3 = self.fill_simple_template(result2, self.resources)
        with open(out_fp, 'w') as f:
            yaml.dump(result3, f, default_flow_style=False)
        print("Completed config_values file written to ", out_fp)
