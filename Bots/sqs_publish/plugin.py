"""
Main plugin module for custom actions
"""
from DivvyPlugins.plugin_metadata import PluginMetadata


class metadata(PluginMetadata):
    """
    Information about this plugin
    """
    version = '1.1'
    last_updated_date = '2019-01-08'
    author = 'Divvycloud'
    nickname = 'AWS SQS Publish'
    default_language_description = 'Allows publishing a message to an SQS queue as an action.'
    category = 'Actions'
    managed = False


def load():
    pass


def unload():
    pass
