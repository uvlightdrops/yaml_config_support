from yaml_config_support.yamlTemplateFillSupport import YamlTemplateFillSupport
#from .yamlTemplateFillSupport import YamlTemplateFillSupport
import yaml
import os
import shutil


class K8sValuesFill(YamlTemplateFillSupport):

    def __init__(self, env, template_dir, creds_dir, options):
        self.template_dir = template_dir
        self.creds_dir = creds_dir
        self.env = env
        self.data = {}
        #self.example()
        self.verbose = False
        if 'verbose' in options:
            self.verbose = options['verbose']
        for key, value in options.items():
            self.out("option %s set to %s" %(key, value))
            setattr(self, key, value)
        #self.verbose = verbose
        #self.data_files = self.options['data_files']

    # method for file loading
    # we need a mapping
    # values_user for example is loaded from creds_dir/values_user.yaml
    # the content shall be applied to the template as an overlay nested dict

    def load_files_spec(self):
        for key, info in self.data_files.items():
            if info['env'] == 'yes':
                env = '_%s' % self.env
            else:
                env = ''
            if info['source'] == 'private':
                fn = '%s/values_%s%s.yaml' % (self.creds_dir, key, env)
                self.out("PRIVATE file: ", fn)
                with open(fn, 'r') as file:
                    self.data[key] = yaml.safe_load(file)
            elif info['source'] == 'project':
                fn = '%s/values_%s%s.yaml' % (self.template_dir, key, env)
                self.out("PROJECT file: ", fn)
                with open(fn, 'r') as file:
                    tmp = yaml.safe_load(file)
                    if info['env'] == 'together':
                        self.data[key] = tmp[self.env]
                    else:
                        self.data[key] = tmp

    def load_files(self):
        # load the template file
        fn = '%s/values_%s.yaml' % (self.template_dir, 'onefitsall')
        with open(fn, 'r') as f:
            self.template = yaml.safe_load(f)
        self.out("TEMPLATE file: ", fn)

        self.load_files_spec()

    def example(self):
        self.data_files = {
            'creds': {
                'source': 'private',
                'transform': 'fill_config_template',
                'env': 'yes',
            },
            'resources': {
                'source': 'project',
                'transform': 'fill_simple_template',
                'env': 'together',
            },
            'user': {
                'source': 'private',
                'transform': 'fill_config_template',
                'env': 'no',
            },
        }

    def fill_configs(self):
        for key, info in self.data_files.items():
            if info['transform'] == 'fill_config_template':
                temp = self.fill_config_template(self.template, self.data[key])
            elif info['transform'] == 'fill_simple_template':
                temp = self.fill_simple_template(self.template, self.data[key])
            else:
                temp = self.template
            self.template = temp

        self.result = self.template

    def write_output(self, out_dir, env):

        out_sub = f'{out_dir}/cf-{env}'
        if not os.path.exists(out_sub):
            os.makedirs(out_sub)

        out_fp = f'{out_sub}/updated_values-{env}.yaml'
        if os.path.exists(out_fp):
            if self.verbose:
                print(f'Target output file existed: {out_fp}, making backup')
            shutil.copy(out_fp, out_fp+'_bak.yaml')


        with open(out_fp, 'w') as f:
            yaml.dump(self.result, f, default_flow_style=False)
        print("Completed config_values file written to ", out_fp)

