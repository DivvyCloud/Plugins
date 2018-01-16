import logging
from datetime import datetime

import requests
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

# REPLACE WITH YOUR REPO.
image_whitelist_url = 'https://s3.amazonaws.com/bfexamples.botfactory.io/approved_images.json'


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
            schedulable=schedule.Periodic(minutes=1)
        )

    @classmethod
    def get_template_id(cls, **job_creation_kwargs):
        """ This provides a unique name to the job """
        return 'harvest-image-validation'

    def image_getter(self):
        """ My custom method for talking to Github """
        response = requests.get(image_whitelist_url, timeout=10)
        return response.json()

    @EscalatePermissions()
    def do_harvest(self):
        print 'we are here'
        with NewSession(DivvyCloudGatewayORM):
            db = DivvyCloudGatewayORM()
            for region_name, image_ids in self.image_getter().items():
                for image_id in image_ids:
                    db.session.merge(dbobjects.ValidImage(
                        region_name=region_name,
                        image_id=image_id
                    ))
            # db.session.commit()

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
    print 'wtf'
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
