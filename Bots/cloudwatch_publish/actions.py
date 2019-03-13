import json
import jinja2
import time

from DivvyBotfactory.event import BotEvent
from DivvyBotfactory.registry import BotFactoryRegistryWrapper
from DivvyBotfactory.scheduling import ScheduledEventTracker, schedule_hours_from_now
from DivvyCloudProviders.Common.Frontend.frontend import get_cloud_type_by_organization_service_id
from DivvyDb.DivvyCloudGatewayORM import DivvyCloudGatewayORM
from DivvyDb import DivvyDbObjects
from DivvyDb.QueryFilters.cloud_types import CloudType
from DivvyUtils.field_definition import (
    FieldOptions, StringField, Jinja2TextField, Jinja2StringField, FloatField
)

registry = BotFactoryRegistryWrapper()


@registry.action(
    uid='divvy.action.publish_to_cloudwatch_logs',
    name='Publish to CloudWatch Logs',
    bulk_action=True,
    description=(
        'Publish a message to a specific CloudWatch log group. Note that this '
        'log group need to be created ahead of time.'
    ),
    author='DivvyCloud Inc.',
    supported_resources=[],
    supported_clouds=[
        CloudType.AMAZON_WEB_SERVICES,
        CloudType.AMAZON_WEB_SERVICES_GOV,
        CloudType.AMAZON_WEB_SERVICES_CHINA
    ],
    settings_config=[
        StringField(
            name='log_group_arn',
            display_name='Log Group ARN',
            options=FieldOptions.REQUIRED,
            description=(
                'The ARN of the target CloudWatch Log Group' 
            )
        ),
        StringField(
            name='stream_name',
            display_name='Stream Name',
            options=FieldOptions.REQUIRED,
            description=(
                'The name of the stream to publish logs into' 
            )
        ),
        Jinja2TextField(
            name='message',
            display_name='Log Message',
            description=(
                'The message payload to send to the topic. Note that Jinja2 '
                'templating is supported.'
            )
        )
    ]
)
def publish_to_cloudwatch_logs(bot, settings, matches, _non_matches):
    # Get a mapping of topic ARNs to organization service IDs
    db = DivvyCloudGatewayORM()
    org_svc_mapping = dict(
        db.session.query(
            DivvyDbObjects.ServiceLogGroup.namespace_id,
            DivvyDbObjects.ServiceLogGroup.organization_service_id
        )
    )
    log_group_arn = settings['log_group_arn']
    region = log_group_arn.split(':')[3]
    log_group_name = log_group_arn.split(':')[-2]
    org_svc_id = org_svc_mapping.get(log_group_arn)
    if not org_svc_id:
        raise ValueError('Unable to identify organization service ID')
    frontend = get_cloud_type_by_organization_service_id(org_svc_id)
    backend = frontend.get_cloud_gw(region_name=region)
    client = backend.client('logs')

    # Get our last sequence token
    response = client.describe_log_streams(
        logGroupName=log_group_name,
        logStreamNamePrefix=settings['stream_name']
    )
    upload_sequence = None
    for item in response.get('logStreams', []):
        if item['logStreamName'] == settings['stream_name']:
            upload_sequence = item['uploadSequenceToken']

    with ScheduledEventTracker() as context:
        for resource in matches:
            event = BotEvent('hookpoint', resource, bot.bot_id, bot.name)
            message = jinja2.Template(settings.get('message', ''))
            response = client.put_log_events(
                logGroupName=log_group_name,
                logStreamName=settings['stream_name'],
                logEvents=[{
                    'timestamp': int(round(time.time() * 1000)),
                    'message': message.render(event=event, resource=resource),
                }],
                sequenceToken=upload_sequence
            )

            upload_sequence = response.get('nextSequenceToken')


def load():
    registry.load()
