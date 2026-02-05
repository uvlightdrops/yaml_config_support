import yaml
from collections import OrderedDict
#from yaml_config_support.output_control import OutputControl
from .output_control import OutputControl

def represent_ordereddict(dumper, data):
    return dumper.represent_dict(data.items())

yaml.add_representer(OrderedDict, represent_ordereddict)


class YamlTemplateFillSupport(OutputControl):
    def fill_config_template(self, template_d, values_d):
        filled_d = OrderedDict()
        for key, value in template_d.items():
            if isinstance(value, dict):
                sub_values_d = values_d.get(key, {})
                filled_d[key] = self.fill_config_template(value, sub_values_d)
            else:
                if key in values_d.keys():
                    filled_d[key] = values_d[key]
                    self.out('INSERTING a value for %s' % key)
                else:
                    filled_d[key] = value
        return filled_d

    def fill_simple_template(self, template_d, values_d):
        def set_nested_value(nested_dict, keys, new_value):
            value = nested_dict
            for key in keys[:-1]:
                value = value[key]
            last_key = keys[-1]
            value[last_key] = new_value

        def set_list2(nested_dict, keys, l_item):
            value = nested_dict
            for key in keys[:-1]:
                value = value[key]
            if len(l_item) > 0 and type(l_item[0]) != dict:
                nested_dict_temp = nested_dict
                for key in keys[:-1]:
                    nested_dict_temp = nested_dict_temp[key]
                last_key = keys[-1]
                nested_dict_temp[last_key] = l_item
                self.out('REPLACED %s items' % (str(len(l_item))))
                return
            value = value[keys[len(keys)-1]]
            for new_dict in l_item:
                match_key = list(new_dict.keys())[0]
                match_value = new_dict[match_key]
                for idx, old_dict in enumerate(value):
                    if old_dict.get(match_key) == match_value:
                        updated = OrderedDict(old_dict)
                        for k, v in new_dict.items():
                            updated[k] = v
                            self.out("UPDATED: %s set to %s" % (k, v))
                        value[idx] = updated
            return
        if 'lists' in values_d.keys():
            for l_key, l_item in values_d['lists'].items():
                keys = l_key.split('.')
                set_list2(template_d, keys, l_item)
            values_d.pop('lists')
        for key, value in values_d.items():
            keys = key.split('.')
            self.out('INSERTING %s %s for %s' % (value, ' '*(6-len(str(value))), key))
            set_nested_value(template_d, keys, value)
        return template_d
