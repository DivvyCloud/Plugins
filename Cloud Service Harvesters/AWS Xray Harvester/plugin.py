"""
Main plugin module for custom actions
"""
from DivvyPlugins.plugin_metadata import PluginMetadata


class metadata(PluginMetadata):
    """
    Information about this plugin
    """
    version = '1.1'
    last_updated_date = '2019-02-22'
    author = 'Divvycloud'
    nickname = 'AWS X-Ray Encryption Configuration'
    default_language_description = 'Retrieves the encryption configuration for X-Ray data'
    category = 'Harvester'
    managed = False


def load():
    pass


def unload():
    pass
