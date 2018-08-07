import boto3
import json
import logging
from datetime import datetime

import requests
from DivvyCloudProviders.Common.Frontend.frontend import get_cloud_type_by_organization_service_id
from DivvyDb.DivvyCloudGatewayORM import DivvyCloudGatewayORM
from DivvyDb.DivvyDb import NewSession, SharedSessionScope
from DivvyJobs.schedules import LazyScheduleGoal
from DivvyPlugins.plugin_helpers import (register_job_module,
                                         unregister_job_module)
from DivvyPlugins.plugin_jobs import PluginHarvester
from DivvySession.DivvySession import EscalatePermissions
from DivvyUtils import schedule

import dbobjects

logger = logging.getLogger('ValidImageHarvest')

# Replace with the path to the JSON. Note that this is only used for unauthenticated
# direct access. For direct access to S3 using authentication, use the values above.
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

    @classmethod
    def get_harvest_schedule(cls, **job_creation_kwargs):
        """ Sets frequency and worker queue """
        return LazyScheduleGoal(
            queue_name='DivvyCloudHarvest',
            schedulable=schedule.Periodic(minutes=30)
        )

    @classmethod
    def get_template_id(cls, **job_creation_kwargs):
        """ This provides a unique name to the job """
        return 'harvest-image-validation'

    def image_getter_unauth(self):
        """ My custom method for talking to Github """
        response = requests.get(image_whitelist_url, timeout=10)
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


@SharedSessionScope(DivvyCloudGatewayORM)
def list_job_templates():
    # Only 1 job template for this job
    job_templates = [
        ValidImageHarvester.create_job_template(),
    ]

    return job_templates


_JOB_LOADED = False


def load():
    global _JOB_LOADED
    try:
        _JOB_LOADED = register_job_module(__name__)
    except AttributeError:
        pass


def unload():
    global _JOB_LOADED
    if _JOB_LOADED:
        unregister_job_module(__name__)
        _JOB_LOADED = False