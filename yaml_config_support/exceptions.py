"""Eigene Ausnahmen für vorhersehbare Fehler im YAML-Fill-Workflow."""


class YamlConfigSupportError(Exception):
    """Basisklasse für fachliche Fehler des Projekts."""


class InvalidOptionsError(YamlConfigSupportError):
    """Die übergebenen Optionen oder Dateispezifikationen sind ungültig."""


class DataFileConfigurationError(YamlConfigSupportError):
    """Eine `data_files`-Definition ist unvollständig oder fachlich inkonsistent."""


class YamlFileAccessError(YamlConfigSupportError):
    """Eine erwartete YAML-Datei fehlt oder kann nicht gelesen werden."""


class MissingEnvironmentError(YamlConfigSupportError):
    """Eine Datei mit mehreren Umgebungen enthält die angeforderte Umgebung nicht."""

