"""Hilfsklassen zum Laden und Füllen von YAML-Konfigurationen."""

try:
	from .yamlConfigSupport import YamlConfigSupport
except ModuleNotFoundError:
	YamlConfigSupport = None
