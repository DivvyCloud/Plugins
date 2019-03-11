import simplejson as json
from datetime import datetime, timedelta

from DivvyApp.DivvyApp import DivvyApp
from DivvyDb import DivvyDbObjects
from DivvyDb.DivvyCloudGatewayORM import DivvyCloudGatewayORM
from DivvyDb.QueryFilters.registry import QueryRegistry
from DivvyResource.resource_types import ResourceType

import dbobjects

default_filters_author = 'DivvyCloud Inc.'

@QueryRegistry.register(
    query_id='custom.filter.instance_running_approved_image',
    name='Instance Running Approved Image',
    description=(
        'Match the image ID of an instance against a list of approved images'
    ),
    author=default_filters_author,
    supported_resources=[ResourceType.INSTANCE],
    settings_config=[]
)
def instance_running_approved_image(query, db_cls, settings_config):
    db = DivvyCloudGatewayORM()
    return query.filter(db_cls.image_id.in_(
        db.session.query(
            dbobjects.ValidImage.image_id
        )
    ))

@QueryRegistry.register(
    query_id='custom.filter.instance_not_running_approved_image',
    name='Instance Not Running Approved Image',
    description=(
        'Identify instances running images which are not valid'
    ),
    author=default_filters_author,
    supported_resources=[ResourceType.INSTANCE],
    settings_config=[]
)
def instance_not_running_approved_image(query, db_cls, settings_config):
    db = DivvyCloudGatewayORM()
    return query.filter(db_cls.image_id.notin_(
        db.session.query(
            dbobjects.ValidImage.image_id
        )
    ))

def load():
    pass

def unload():
    # Unload filters
    QueryRegistry.unregister('custom.filter.instance_running_approved_image')
    QueryRegistry.unregister('custom.filter.instance_not_running_approved_image')
    pass
