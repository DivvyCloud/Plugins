import boto3
import json
import logging

import requests
from DivvyCloudProviders.Common.Frontend.frontend import get_cloud_type_by_organization_service_id
from DivvyDb.DivvyCloudGatewayORM import DivvyCloudGatewayORM
from DivvyDb.DivvyDb import NewSession
from DivvyPlugins.plugin_jobs import PluginHarvester
from DivvySession.DivvySession import EscalatePermissions

from scheduler import client
from worker.registry import Router


import dbobjects

logger = logging.getLogger('ValidImageHarvest')

# Replace with the path to the JSON. Note that this is only used for unauthenticated
# direct access. For direct access to S3 using authentication, use the values below.
IMAGE_WHITELIST_URL = 'https://s3.amazonaws.com/bfexamples.botfactory.io/approved_images.json'

# Replace with Oranization service ID, bucket name, prefix and where to save the file
ORGANIZATION_SERVICE_ID = 82
S3_BUCKET_NAME = 'bfexamples.botfactory.io'
S3_BUCKET_REGION = 'us-east-1'
FILE_KEY = 'approved_images.json'


class ValidImageHarvester(PluginHarvester):

    def __init__(self):
        super(ValidImageHarvester, self).__init__()

    def _setup(self):
        """
        Override to perform setup operations in the worker process
        """
        super(ValidImageHarvester, self)._setup()

    def image_getter_unauth(self):
        """ My custom method for talking to Github """
        response = requests.get(IMAGE_WHITELIST_URL, timeout=10)
        return response.json()

    def image_getter_auth(self):
        # Get the credentials for the supplied organization service
        frontend = get_cloud_type_by_organization_service_id(
            ORGANIZATION_SERVICE_ID
        )
        backend = frontend.get_cloud_gw()

        # Form boto connection and list buckets
        client = boto3.client(
            's3',
            aws_access_key_id=backend.auth_api_key,
            aws_secret_access_key=backend.auth_secret,
            aws_session_token=backend.session_token,
            region_name=S3_BUCKET_REGION
        )

        client.download_file(
            S3_BUCKET_NAME,
            FILE_KEY,
            '/tmp/whitelisted_images.json'
        )

        # Read file from disk and return so we can process it
        json_data = open('/tmp/whitelisted_images.json').read()
        return json.loads(json_data)

    @EscalatePermissions()
    def do_harvest(self):
        with NewSession(DivvyCloudGatewayORM):
            db = DivvyCloudGatewayORM()
            if ORGANIZATION_SERVICE_ID and S3_BUCKET_NAME and FILE_KEY:
                for region_name, image_ids in self.image_getter_auth().items():
                    for image_id in image_ids:
                        db.session.merge(dbobjects.ValidImage(
                            region_name=region_name,
                            image_id=image_id
                        ))
            else:
                for region_name, image_ids in self.image_getter_unauth().items():
                    for image_id in image_ids:
                        db.session.merge(dbobjects.ValidImage(
                            region_name=region_name,
                            image_id=image_id
                        ))

    def _cleanup(self):
        super(ValidImageHarvester, self)._cleanup()


def load():
    Router.add_job(ValidImageHarvester)
    client.add_periodic_job(ValidImageHarvester.__name__, args={}, interval=30)


def unload():
    pass
