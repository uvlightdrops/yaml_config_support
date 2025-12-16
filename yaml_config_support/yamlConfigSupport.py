import os
import glob
import re
import yaml
from flowpy.utils import setup_logger
from pathlib import Path, PosixPath
import collections

logger = setup_logger(__name__, __name__+'.log')

def posixpath_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))
yaml.add_representer(PosixPath, posixpath_representer)

def represent_ordereddict(dumper, data):
    return dumper.represent_dict(data.items())
yaml.add_representer(collections.OrderedDict, represent_ordereddict)

# XXX add pydantic support, maybe use yaml_validate.py script
class YamlConfigSupport:
    """ supports loading yaml config files, and setting them as class members
        loading complete deirectories of yaml files,
        and laoding several cfg layers, for example for inheritance"""
    # XXX rm ?
    # defaults
    # config_dir = Path(__file__).parent
    # config_dir_master = ''
    cfg_local = {}
    # ok to set here default, needed for StockManager app
    phase_subdir = ''
    config_d = {}

    def ycs_setup_base(self, config_dir):
        self.config_dir = config_dir

    # click section
    def config_list(self):
        """ show all config keys, for click command line """
        logger.debug('self.config_d.keys(): %s', self.config_d.keys())
        # return list(self.config_d.keys())
        return sorted(self.config_d.keys())


    def config_show(self, cfg_name):
        """ show config dict for given name, for click command line """
        if cfg_name not in self.config_d:
            return f'Config {cfg_name} not found.'
        else:
            logger.debug('self.config_d[cfg_name]: %s', self.config_d[cfg_name])
            # return self.config_d[cfg_name]
            return yaml.dump(self.config_d[cfg_name], default_flow_style=False)

    def reload_configs(self):
        """ reload all configs, for example after changing phase """
        self.fnlist = self.load_config('fnlist.yml', phase_subdir='')['fnlist']
        self.cache_configs(self.fnlist)

    # main config control method
    def cache_configs(self, fnlist):
        # keep this list for later use
        # self.config_names_list = fnlist
        # set as default if no phase is given
        self.cfg_names_list = fnlist
        logger.debug('self.phase: %s', self.phase)
        if self.phase:
            self.overlay_phase_cfg(fnlist)

        # Reset subdir again, so other parts of the code access the default cfg
        self.phase_subdir = ''
        logger.debug('fnlist, reduced by fn_spec_l: %s', self.cfg_names_list)
        # MAIN thing and idea:
        self.set_configs_as_members(self.cfg_names_list)

        self.set_phase_subdir()

        if self.app_type == 'tree':
            pass
            self.additional_yaml_config_logic()

        # Local overlay dict
        # logger.debug('self.cfg_local.keys(): %s', self.cfg_local.keys())
        if self.cfg_local:
            logger.debug('local.yml has content')
            self.apply_local()

        # XXX self.cfg_local not defined without phase arg
        # OFF ypipe # self.cfg_si = self.cfg_kp_si
        self.cfg_si = self.cfg_kp_si
        # A meta config / also files and paths
        # self.cfg_si = self.load_config('cfg_si.yml')
        # MASTER configs
        self.cfg_master = {}
        for cfg in self.cfg_si['cfg_master_files']:
            # logger.debug('loading master config %s', cfg)
            self.cfg_master[cfg] = self.load_config_master(cfg+'.yml')
            self.cfg_age = self.cfg_master['vals_a-g-e']
        #self.cfg_meta = self.load_config('kp_meta.yml')
        # DATA DIR configs XXX intransparent , set in application code
        self.cfg_si['data_in'] = Path(self.data_path).joinpath('data_in')
        self.cfg_si['data_in_sub'] = self.cfg_si['data_in'].joinpath(self.sub)
        #self.cfg_si['data_in'] = Path(self.cfg_si['data_path']).joinpath('data_in', self.sub)
        self.cfg_si['data_out'] = Path(self.data_path).joinpath('data_out')
        self.cfg_si['data_out_sub'] = self.cfg_si['data_out'].joinpath(self.sub)
        #self.cfg_si['data_out'] = Path(self.cfg_si['data_path']).joinpath('data_out_sub', self.sub)
        # removed
        self.profile_name = self.cfg_si['profile_name']

    def get_phases_bydirs(self):
        subdirs = glob.glob('p*', root_dir=self.config_dir)
        for subdir in subdirs:
            logger.debug('subdir: %s', subdir)
            # if re.match('p\d+', subdir):
            if re.match('p\d+(_.*)?', subdir):
                print(subdir)
            else:
                logger.debug('skipped phase subdir: %s', subdir)

    def set_phase_subdir(self):
        logger.debug('phase: %s  || phase_subdir: %s', self.phase, self.phase_subdir)
        # if len(self.phase.split('_')) == 1:
        if re.match('p\d+', self.phase):
            # the condition means, if just ie p3 is given and not p3_mysepcialphase
            p_subdirs = glob.glob(self.phase + '_*', root_dir=self.config_dir)
            if len(p_subdirs) > 1:
                # this case is not wanted
                self.phase_subdir = p_subdirs[0]
            else:
                self.phase_subdir = p_subdirs[0]
            logger.debug('Overlay cfg with yml files in %s', self.phase_subdir)

    # if there is a phase subdir, load cfg preferred from there
    def overlay_phase_cfg(self, fnlist):
        self.phase_subdir = self.phase
        self.set_phase_subdir()
        phase_cfg_dir = self.config_dir.joinpath(self.phase_subdir)
        # if os.path.exists(phase_cfg_dir):
        if phase_cfg_dir.exists():
            # yml_list = os.listdir(phase_cfg_dir)
            yml_list = phase_cfg_dir.glob('kp_*.yml')
            fn_spec_l = []
            #logger.debug('yml_list %s', dir(yml_list))
            for x in list(yml_list):
                nn = x.name[:-4]
                logger.debug('nn: %s', nn)
                fn_spec_l.append(nn)
            # fn_spec_l = [x.name[:-4] for x in yml_list]
            logger.debug('fn_spec_l: %s', fn_spec_l)

            self.set_configs_as_members(fn_spec_l)
            # calc remaining cfg - will load from default dir
            self.cfg_names_list = [x for x in fnlist if x not in fn_spec_l]
            logger.debug('self.cfg_names_list: %s', self.cfg_names_list)
        # self.cfg_si = self.load_config('cfg_si.yml')

        # if exist, load local.yml cfg
        fn_local = 'local.yml'
        if phase_cfg_dir.joinpath(fn_local).exists():
            self.cfg_local = self.load_config(fn_local)

    # put the group_logic_*.yml files as sub dicts into the wanted_logic dict
    # XXX Abstract this!! The cfg_kp_logic_ctrl_groups  has nothing to do with basic yaml config issues
    #  def hack_wanted_logic(self):
    # moved to treeReorderBuilder

    def init_config_profile(self):
        # loads main config for profile support
        fn = 'config_dp.yml'
        scriptdir = self.master_config_dir
        #scriptdir = os.path.dirname(os.path.realpath(__file__))
        cfg_profile_dir = Path(scriptdir)
        with open(cfg_profile_dir.joinpath(fn)) as f:
                self.cfg_dp = yaml.safe_load(f)
        cfg_default = self.cfg_dp['default_profile']

        #profile = self.cfg_dp['profile']
        # use profile name given from app config
        profile = self.profile_name
        if profile is None:
            self.cfg_profile = cfg_default
        else:
            self.cfg_profile = self.cfg_dp[profile]
            # for missing keys in specific profile, use the default value
            for key in cfg_default.keys():
                if key not in self.cfg_profile:
                    self.cfg_profile[key] = cfg_default[key]

    def set_configs_as_members(self, cfg_names_list=[]):
        """ set all given names as class members and load all dicts from yaml files """
        self.cfg_names_list = cfg_names_list
        for name in cfg_names_list:
            fn = name + '.yml'
            self.config_d[name] = self.load_config(fn)
        for name in cfg_names_list:
            # logger.debug('loading config %s, set as %s', fn, 'cfg_'+name)
            setattr(self, 'cfg_'+name, self.config_d[name])
            # logger.debug('cfg_%s: %s', name, getattr(self, 'cfg_'+name))

    def load_config(self, filename, phase_subdir=None):
        """ load from set config_dir, optional subdir for phase auto-added """
        if phase_subdir is None:
            phase_subdir = self.phase_subdir
        path = self.config_dir.joinpath(phase_subdir, filename)
        logger.debug('attempt to load config file %s ', path)
        with open(path) as f:
            config = yaml.safe_load(f)
        return config

    def load_config_master(self, filename):
        """ load config from master directory"""
        path = self.master_config_dir.joinpath(filename)
        with open(path) as f:
            # logger.debug('loading config file %s from dir %s', f.name, self.config_dir)
            config = yaml.safe_load(f)
        return config

    def load_config_from_dirs(self, directories):
        """ solution for inheritance in the yaml dict """
        config = {}
        for directory in directories:
            yaml_files = glob.glob(os.path.join(directory, "*.yml"))
            # logger.debug('yaml_files: %s', yaml_files)
            for yaml_file in yaml_files:
                #logger.debug('loading config file %s', yaml_file)
                try:
                    with open(yaml_file, 'r') as f:
                        config.update(yaml.safe_load(f))
                except:
                    logger.warning('error loading file %s', yaml_file)
        return config

    # cache_configs is already run, now load overlay dict
    def apply_local(self):
        logger.debug('self.cfg_local.keys(): %s', self.cfg_local.keys())
        # check all known cfg names
        for cfg_name in self.cfg_names_list: #  + ['si']:
            # if current cfg name exist as key in local cfg dict
            # logger.debug('cfg_name: %s', cfg_name)
            if cfg_name in self.cfg_local.keys():
                logger.debug('cfg_name: %s', cfg_name)
                # assign the current section of default cfg to a tmp var
                cfg_cur = getattr(self, 'cfg_'+cfg_name)
                #logger.debug('cfg_cur.keys(): %s', cfg_cur.keys())
                # assign the section of local cfg to a tmp var
                cfg_local = self.cfg_local[cfg_name]
                # update the dict of default cfg with the changed values
                cfg_cur.update(cfg_local)
                setattr(self, 'cfg_'+cfg_name, cfg_cur)
                yaml_str = yaml.dump(cfg_cur, default_flow_style=False)
                # logger.debug(yaml_str)
                yaml_str = yaml.dump(self.cfg_local, default_flow_style=False)
                # logger.debug(yaml_str)
                logger.debug("--------------------------------------")

    # a method to fill in values in a yaml config dict,
    # we pass the template dict and a values dict
    # the result should be in same order as original template
    # The values dict contains only the keys and values to be replaced
    # this needs to be done recursively for all nested dict levels
    def fill_config_template(self, template_d, values_d):
        from collections import OrderedDict
        filled_d = OrderedDict()
        for key, value in template_d.items():
            if isinstance(value, dict):
                # recursive call for nested dict
                sub_values_d = values_d.get(key, {})
                filled_d[key] = self.fill_config_template(value, sub_values_d)
            else:
                # replace value if key exists in values_d
                filled_d[key] = values_d.get(key, value)
        return filled_d

