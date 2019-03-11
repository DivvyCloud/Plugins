"""
Main plugin module for Image Whitelisting
"""
from DivvyPlugins.plugin_metadata import PluginMetadata
from DivvyPlugins.settings import GlobalSetting
from DivvyResource.Resources import DivvyPlugin


class metadata(PluginMetadata):
    """
    Information about this plugin
    """
    version = '1.0'
    last_updated_date = '2015-08-05'
    author = 'DivvyCloud Inc.'
    nickname = 'DivvyCloud Image Whitelist'
    default_language_description = (
        'Fetches approved images from a remote location.'
    )
    support_email = 'support@divvycloud.com'
    support_url = 'http://support.divvycloud.com'
    main_url = 'http://www.divvycloud.com'
    category = 'Reports'
    managed = True


# Prefix for settings used by this plugin
_SETTING_PREFIX = DivvyPlugin.get_current_plugin().name

# Settings
SETTING_HARVEST_LOCATION = '%s.harvest_location' % _SETTING_PREFIX
IMAGE_WHITELIST_URL = GlobalSetting(
    name=SETTING_HARVEST_LOCATION,
    display_name='URL to Image Listing',
    type_hint='string',
    description='URL to fetch the image whitelist listing'
)

def load():
    pass


def unload():
    pass
