import logging

import boto3

from DivvyCloudProviders.Common.Frontend.frontend import get_cloud_type_by_organization_service_id
from DivvyDb import DivvyDbObjects
from DivvyDb.DivvyCloudGatewayORM import DivvyCloudGatewayORM
from DivvyDb.DivvyDb import NewSession, SharedSessionScope
from DivvyPlugins.plugin_jobs import PluginJob
from DivvyResource import ResourceIds
from scheduler import client
from worker.registry import Router

logger = logging.getLogger(__name__)


class XRayEncryptionConfigProcessor(PluginJob):

    def __init__(self):
        super(XRayEncryptionConfigProcessor, self).__init__()

    @SharedSessionScope(DivvyCloudGatewayORM)
    def run(self):
        """
        Job implementations must implement this method to perform their work
        """
        with NewSession(DivvyCloudGatewayORM):
            db = DivvyCloudGatewayORM()

            org_services = db.session.query(
                DivvyDbObjects.OrganizationService.organization_service_id,
                DivvyDbObjects.OrganizationService.name
            ).filter(
                DivvyDbObjects.OrganizationService.cloud_type_id == 'AWS'
            ).filter(
                DivvyDbObjects.OrganizationService.status.notin_([
                    DivvyDbObjects.OrganizationService.Status.DELETE,
                    DivvyDbObjects.OrganizationService.Status.PAUSED,
                    DivvyDbObjects.OrganizationService.Status.INVALID_CREDS,
                    DivvyDbObjects.OrganizationService.Status.ASSUME_ROLE_FAIL
                ])
            )

            for org_service in org_services:

                logger.info('Harvesting X-Ray encryption configuration for %s', org_service.name)

                frontend = get_cloud_type_by_organization_service_id(
                    org_service.organization_service_id
                )

                for region in frontend.get_compute_regions():
                    backend = frontend.get_cloud_gw(region_name=region)

                    client = boto3.client(
                        'xray',
                        aws_access_key_id=backend.auth_api_key,
                        aws_secret_access_key=backend.auth_secret,
                        aws_session_token=backend.session_token,
                        region_name=region
                    )

                    encryption_type = client.get_encryption_config()['EncryptionConfig']['Type']
                    resource_id = ResourceIds.ServiceRegion(
                        organization_service_id=org_service.organization_service_id,
                        region=region
                    )

                    db.session.merge(DivvyDbObjects.ResourceProperty(
                        resource_id=resource_id,
                        name='custom.xray_encryption_config_type',
                        value=encryption_type,
                        type_hint='string'
                    ))
                    db.session.commit()


def load():
    Router.add_job(XRayEncryptionConfigProcessor)
    client.add_periodic_job(XRayEncryptionConfigProcessor.__name__, args={}, interval=120)


def unload():
    pass
