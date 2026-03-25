"""Lädt Wertedateien und kombiniert sie zu einer finalen Kubernetes-Values-Datei."""

from yaml_config_support.yamlTemplateFillSupport import YamlTemplateFillSupport
#from .yamlTemplateFillSupport import YamlTemplateFillSupport
import yaml
import os
import shutil


class K8sValuesFill(YamlTemplateFillSupport):
    """Orchestriert das Laden, Überlagern und Schreiben von Values-Dateien.

    Die Klasse erwartet ein Basistemplate namens ``values_onefitsall.yaml`` im
    Template-Verzeichnis. Weitere Dateien werden über ``data_files`` beschrieben.
    Deren Reihenfolge bestimmt auch die Reihenfolge der Overlays.
    """

    def __init__(self, env, template_dir, creds_dir, options):
        """Initialisiert den Füllprozess für eine Zielumgebung.

        Args:
            env: Zielumgebung wie ``dev`` oder ``prod``.
            template_dir: Verzeichnis mit Template- und Projektdateien.
            creds_dir: Verzeichnis mit privaten Wertedateien.
            options: Konfigurationsdictionary; relevante Schlüssel sind unter
                anderem ``verbose`` und ``data_files``.
        """
        super().__init__(verbose=options.get('verbose', False))
        self.template_dir = template_dir
        self.creds_dir = creds_dir
        self.env = env
        self.data = {}
        #self.example()
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
        """Lädt alle in ``data_files`` beschriebenen Overlay-Dateien.

        Dateinamenskonventionen:

        * ``values_<key>_<env>.yaml`` bei ``env == 'yes'``
        * ``values_<key>.yaml`` bei ``env == 'no'`` oder ``'together'``

        Für Projektdateien mit ``env == 'together'`` wird aus der geladenen
        Datei nur der Abschnitt der aktuellen Umgebung übernommen.
        """
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
        """Lädt das Basistemplate und anschließend alle Overlay-Dateien."""
        # load the template file
        fn = '%s/values_%s.yaml' % (self.template_dir, 'onefitsall')
        with open(fn, 'r') as f:
            self.template = yaml.safe_load(f)
        self.out("TEMPLATE file: ", fn)

        self.load_files_spec()

    def example(self):
        """Setzt ein Beispiel für ``data_files`` direkt auf der Instanz.

        Die Methode dient als Referenz für die erwartete Struktur von
        ``data_files`` und wird aktuell nicht automatisch aufgerufen.
        """
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
        """Wendet alle konfigurierten Overlays in definierter Reihenfolge an."""
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
        """Schreibt die berechnete Values-Datei in das Ausgabeziel.

        Die Ausgabe erfolgt nach ``<out_dir>/cf-<env>/updated_values-<env>.yaml``.
        Existiert die Datei bereits, wird vor dem Überschreiben eine Sicherung
        ``*_bak.yaml`` angelegt.

        Args:
            out_dir: Basisverzeichnis für die Ausgabe.
            env: Name der Zielumgebung; wird in Pfad und Dateiname verwendet.
        """

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

