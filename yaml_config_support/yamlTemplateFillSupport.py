"""Hilfsfunktionen zum Füllen von YAML-Templates mit Wertedateien."""

import re
from collections import OrderedDict

import yaml

from .exceptions import PathNotFoundError
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
                if key in values_d:
                    filled_d[key] = values_d[key]
                    self.out('INSERTING a value for %s' % key)
                else:
                    filled_d[key] = value
        return filled_d

    def _parse_path_key(self, key):
        """Zerlegt einen Pfadschlüssel in Dict-Key und optionalen Listenindex.

        Beispiel: ``containers[0]`` → ``('containers', 0)``
        Beispiel: ``spec``          → ``('spec', None)``

        Args:
            key: Ein einzelnes Pfadsegment, ggf. mit ``[N]``-Suffix.

        Returns:
            Tuple ``(dict_key, list_index)`` wobei ``list_index`` ``None`` ist,
            wenn kein Listenindex angegeben wurde.
        """
        match = re.match(r'^(.+)\[(\d+)\]$', key)
        if match:
            return match.group(1), int(match.group(2))
        return key, None

    def _navigate_path(self, nested, keys):
        """Navigiert ein verschachteltes Dict/List-Objekt entlang eines Pfades.

        Unterstützt Listenindizes der Form ``containers[0]``.

        Args:
            nested: Ausgangsobjekt (Dict oder List).
            keys: Liste von Pfadsegmenten.

        Returns:
            Das Objekt am Zielpfad.

        Raises:
            PathNotFoundError: Wenn ein Pfadsegment nicht gefunden wird.
        """
        current = nested
        for key in keys:
            dict_key, list_idx = self._parse_path_key(key)
            try:
                current = current[dict_key]
            except (KeyError, TypeError, IndexError):
                raise PathNotFoundError(
                    f"Pfadsegment '{dict_key}' nicht gefunden in: {list(current.keys()) if isinstance(current, dict) else type(current).__name__}"
                )
            if list_idx is not None:
                try:
                    current = current[list_idx]
                except (IndexError, TypeError):
                    raise PathNotFoundError(
                        f"Listenindex [{list_idx}] für '{dict_key}' nicht erreichbar"
                    )
        return current

    def _set_nested_value(self, nested_dict, keys, new_value):
        """Setzt einen Wert in einem verschachtelten Dictionary per Schlüsselpfad.

        Unterstützt Listenindizes der Form ``containers[0]`` im Pfad.

        Args:
            nested_dict: Ausgangsobjekt.
            keys: Liste von Pfadsegmenten.
            new_value: Zu setzender Wert.

        Raises:
            PathNotFoundError: Wenn ein Zwischenpfad nicht existiert.
        """
        parent = self._navigate_path(nested_dict, keys[:-1])
        final_key, list_idx = self._parse_path_key(keys[-1])
        if list_idx is not None:
            if not isinstance(parent.get(final_key), list):
                raise PathNotFoundError(
                    f"'{final_key}' ist keine Liste – Listenindex [{list_idx}] nicht möglich"
                )
            try:
                parent[final_key][list_idx] = new_value
            except IndexError:
                raise PathNotFoundError(
                    f"Listenindex [{list_idx}] für '{final_key}' außerhalb des Bereichs (Länge: {len(parent[final_key])})"
                )
        else:
            if isinstance(parent, dict) and final_key not in parent:
                available = sorted(parent.keys())
                raise PathNotFoundError(
                    f"Schlüssel '{final_key}' existiert nicht im Template. "
                    f"Vorhandene Schlüssel: {available}"
                )
            parent[final_key] = new_value

    def _set_list_value(self, nested_dict, keys, list_items):
        """Aktualisiert eine Listenstruktur im Template anhand eines Pfads.

        Primitive Listen werden vollständig ersetzt. Bei Listen aus Dictionaries
        werden Einträge über den ersten Schlüssel des neuen Dicts gematcht und
        anschließend feldweise überschrieben.

        Unterstützt Listenindizes der Form ``containers[0]`` im Pfad.
        """
        parent = self._navigate_path(nested_dict, keys[:-1])
        final_key, list_idx = self._parse_path_key(keys[-1])
        target = parent[final_key]

        if list_items and not isinstance(list_items[0], dict):
            parent[final_key] = list_items
            self.out('REPLACED %s items' % str(len(list_items)))
            return

        current_items = target
        for new_dict in list_items:
            match_key = list(new_dict.keys())[0]
            match_value = new_dict[match_key]
            for idx, old_dict in enumerate(current_items):
                if old_dict.get(match_key) == match_value:
                    updated = OrderedDict(old_dict)
                    for key, value in new_dict.items():
                        updated[key] = value
                        self.out("UPDATED: %s set to %s" % (key, value))
                    current_items[idx] = updated

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
        working_values = dict(values_d)
        list_values = working_values.pop('lists', {})

        for l_key, l_item in list_values.items():
            keys = l_key.split('.')
            self._set_list_value(template_d, keys, l_item)

        for key, value in working_values.items():
            keys = key.split('.')
            self.out('INSERTING %s %s for %s' % (value, ' '*(6-len(str(value))), key))
            self._set_nested_value(template_d, keys, value)
        return template_d
