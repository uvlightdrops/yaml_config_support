"""Hilfsfunktionen zum Füllen von YAML-Templates mit Wertedateien."""

import yaml
from collections import OrderedDict
#from yaml_config_support.output_control import OutputControl
from .output_control import OutputControl

def represent_ordereddict(dumper, data):
    """Serialisiert ``OrderedDict``-Instanzen mit stabiler Schlüsselreihenfolge.

    Args:
        dumper: YAML-Dumper-Instanz.
        data: Zu serialisierendes ``OrderedDict``.

    Returns:
        YAML-Repräsentation des Dictionaries.
    """
    return dumper.represent_dict(data.items())

yaml.add_representer(OrderedDict, represent_ordereddict)


class YamlTemplateFillSupport(OutputControl):
    """Bietet zwei Strategien zum Überlagern von YAML-Templates."""

    def __init__(self, verbose=False):
        """Initialisiert die Template-Unterstützung mit optionalem Logging.

        Args:
            verbose: Aktiviert bei ``True`` die Ausgabe über :class:`OutputControl`.
        """
        super().__init__(verbose=verbose)

    def fill_config_template(self, template_d, values_d):
        """Füllt ein verschachteltes Template rekursiv mit Werten gleicher Struktur.

        Nur Schlüssel, die bereits im Template existieren und in ``values_d``
        vorhanden sind, werden überschrieben. Nicht gesetzte Werte bleiben aus
        dem Template erhalten.

        Args:
            template_d: Verschachteltes Template-Dictionary.
            values_d: Overlay-Dictionary mit derselben Grundstruktur.

        Returns:
            ``OrderedDict`` mit den angewendeten Ersetzungen.
        """
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
        """Füllt ein Template über Punktpfade und optionale Listen-Updates.

        ``values_d`` darf flache Schlüssel in Punktnotation enthalten, etwa
        ``resources.limits.cpu``. Zusätzlich kann ein Spezialschlüssel
        ``lists`` verwendet werden, um bestehende Listen im Template entweder
        komplett zu ersetzen oder einzelne Dict-Einträge anhand des jeweils
        ersten Schlüssels zu aktualisieren.

        Args:
            template_d: Das zu verändernde Template-Dictionary.
            values_d: Punktpfad-basiertes Overlay inklusive optionalem
                ``lists``-Abschnitt.

        Returns:
            Das direkt veränderte Template-Dictionary.
        """
        def set_nested_value(nested_dict, keys, new_value):
            """Setzt einen Wert in einem verschachtelten Dictionary per Pfad."""
            value = nested_dict
            for key in keys[:-1]:
                value = value[key]
            last_key = keys[-1]
            value[last_key] = new_value

        def set_list2(nested_dict, keys, l_item):
            """Aktualisiert eine Listenstruktur im Template anhand eines Pfads.

            Primitive Listen werden vollständig ersetzt. Bei Listen aus
            Dictionaries werden Einträge über den ersten Schlüssel des neuen
            Dicts gematcht und dann feldweise überschrieben.
            """
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
