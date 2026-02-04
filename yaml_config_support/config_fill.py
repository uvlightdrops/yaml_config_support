import yaml
import argparse
import os
import shutil
from collections import OrderedDict


home = os.environ['HOME']
### XXX SET here the subpath to your local checked out git repo
subpath_string = 'dev'

basedir = '%s/%s/eip-konfigurationen/codefy/helmchart' %(home, subpath_string)
print("Your basedir ist : ", basedir)

def represent_ordereddict(dumper, data):
    return dumper.represent_dict(data.items())

yaml.add_representer(OrderedDict, represent_ordereddict)

DEBUG=False


class OutputControl:
    def out(self, *args):
        if self.verbose or DEBUG:

            print('LOG '+' '.join(args))



class YamlConfigSupport(OutputControl):
    def fill_config_template(self, template_d, values_d):
        filled_d = OrderedDict()
        for key, value in template_d.items():
            if isinstance(value, dict):
                sub_values_d = values_d.get(key, {})

                # recursive call for nested dict
                filled_d[key] = self.fill_config_template(value, sub_values_d)

            else:
                # replace value if key exists in values_d
                #filled_d[key] = values_d.get(key, value)
                if key in values_d.keys():
                    filled_d[key] = values_d[key]
                    self.out('INSERTING a value for %s' %key)
                else:
                    filled_d[key] = value

        return filled_d


    def fill_simple_template(self, template_d, values_d):

        def set_nested_value(nested_dict, keys, new_value):
            value = nested_dict
            for key in keys[:-1]:
                value = value[key]
            # Set the new value at the last key
            last_key = keys[-1]
            #print(last_key)
            value[last_key] = new_value


        def set_list2(nested_dict, keys, l_item):
            value = nested_dict
            for key in keys:
                value = value[key]
            # value ist jetzt die Liste
            # first check if we have a list of strings (contr. to a list of dicts)

            for new_dict in l_item:
                # einzelitems in diesere liste
                #if type(new_dict) == str:
                    #value.append()
                #self.out(str(new_dict))
                # Das erste Key-Value-Paar dient als Kriterium
                match_key = list(new_dict.keys())[0]
                match_value = new_dict[match_key]
                for idx, old_dict in enumerate(value):
                    if old_dict.get(match_key) == match_value:
                        # Erstelle ein neues OrderedDict, das die Reihenfolge erhält
                        updated = OrderedDict(old_dict)
                        for k, v in new_dict.items():
                            updated[k] = v
                            self.out("UPDATED: %s set to %s" %(k, v))
                        value[idx] = updated

        #print("SUB list")  
        if 'lists' in values_d.keys():
            for l_key, l_item in values_d['lists'].items():
                #print(l_key, l_item)
                keys = l_key.split('.')
                #set_list_nested_value(template_d, keys, values_d)
                set_list2(template_d, keys, l_item)

            values_d.pop('lists')


        #print("SUB dicts")
        for key, value in values_d.items():

            keys = key.split('.')
            self.out('INSERTING %s %s for %s' %(value, ' '*(6-len(str(value))), key))
            set_nested_value(template_d, keys, value)

        return template_d
        



class ConfigFillTest(YamlConfigSupport):
    def __init__(self, template_dir, creds_dir, env='dev'):
        self.template_dir   = template_dir
        self.creds_dir      = creds_dir
        self.env = env
        
    def load_files(self):
        fn = '%s/values_%s.yaml' %(self.template_dir, self.env)
        self.out("TEMPLATE file: ", fn)
        with open(fn, 'r') as f:
            self.template = yaml.safe_load(f)

        fn = '%s/values_resources.yaml' %(self.template_dir) #, self.env)
        self.out("RESOURCES file: "+fn)
        with open(fn, 'r') as f:
            res_yaml = yaml.safe_load(f)
            self.resources = res_yaml[self.env]

        # Load vars in yaml structure for creds
        fn = '%s/values_creds_%s.yaml' %(self.creds_dir, self.env) 
        self.out("CREDS file:    ", fn)
        with open(fn, 'r') as f:
            self.creds = yaml.safe_load(f)

        fn = '%s/values_user.yaml' %(self.creds_dir) 
        self.out("USER file:     ", fn)
        with open(fn, 'r') as f:
            self.user = yaml.safe_load(f)



    def test_config_fill(self, out_fp):
        # substitution in yaml dict
        result  = self.fill_config_template(self.template, self.creds)

        result2 = self.fill_config_template(result, self.user)

        result3 = self.fill_simple_template(result2, self.resources)

        with open(out_fp+'_2.yaml', 'w') as f:
            yaml.dump(result2, f)

        with open(out_fp, 'w') as f:
            yaml.dump(result3, f)

        print("Completed config_values file written to ", out_fp)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Config Fill")
    parser.add_argument("env", help="Environment to use (prod, test, dev)")
    
    default_template_dir = basedir
    parser.add_argument('--template_dir', type=str, default=default_template_dir, 
                        help='Path to the template main dir (git) ')

    default_valuestore_dir = home+'/codefy_creds'
    parser.add_argument('--valuestore_dir', type=str, default=default_valuestore_dir,
                        help='Path to the dir which hold the valuesstores yaml')

    parser.add_argument("-o", "--outdir", help="Directory for output")
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose output: Show each substitution", default=False)

    args = parser.parse_args()
    outpath = '%s/cf/cf-%s' %(home, args.env)
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    if args.outdir:
        outpath = args.outdir

    out_fp = '%s/updated_values-%s.yaml' %(outpath, args.env)
    if os.path.exists(out_fp):
        if args.verbose:
            print('Target output file existed: %s, making backup' %out_fp)
        shutil.copy(out_fp, out_fp+'_bak.yaml')

    template_dir = f'{args.template_dir}' #/{args.env}'

    creds_dir = args.valuestore_dir

    CF = ConfigFillTest(template_dir, creds_dir, env=args.env)
    CF.verbose = args.verbose

    CF.load_files()
    CF.test_config_fill(out_fp)


