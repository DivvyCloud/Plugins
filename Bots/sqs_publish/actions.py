import json
import jinja2
import time
from typing import Dict, Any
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
    uid='divvy.action.publish_to_sqs_queue',
    name='Publish to SQS Queue',
    bulk_action=True,
    description=(
        'Publish a message to a specific SQS queue. Note that this '
        'queue needs to be created ahead of time.'
    ),
    author='Divyv Cloud Corp.',
    supported_resources=[],
    supported_clouds=[
        CloudType.AMAZON_WEB_SERVICES,
        CloudType.AMAZON_WEB_SERVICES_GOV,
        CloudType.AMAZON_WEB_SERVICES_CHINA
    ],
    settings_config=[
        StringField(
            name='message_queue_arn',
            display_name='Message Queue ARN',
            options=FieldOptions.REQUIRED,
            description=(
                'The ARN of the target SQS Queue'
            )
        ),
        Jinja2TextField(
            name='message',
            display_name='Queue Message',
            description=(
                'The message payload to send to the queue. Note that Jinja2 '
                'templating is supported.'
            )
        )
    ]
)
def publish_to_sqs_queue(bot, settings, matches, _non_matches):
    # Get a mapping of topic ARNs to organization service IDs
    db = DivvyCloudGatewayORM()
    org_svc_mapping = dict(
        db.session.query(
            DivvyDbObjects.MessageQueue.arn,
            DivvyDbObjects.MessageQueue.organization_service_id
        )
    )

    queue = db.session.query(
        DivvyDbObjects.MessageQueue.url,
        DivvyDbObjects.MessageQueue.organization_service_id
    ).filter(
        DivvyDbObjects.MessageQueue.arn == settings['message_queue_arn']
    ).first()

    if not queue:
        raise ValueError('Unable to identify this message queue within DivvyCloud')

    message_queue_arn = settings['message_queue_arn']
    region = message_queue_arn.split(':')[2]
    org_svc_id = org_svc_mapping.get(message_queue_arn)
    if not org_svc_id:
        raise ValueError('Unable to identify organization service ID')
    frontend = get_cloud_type_by_organization_service_id(org_svc_id)
    backend = frontend.get_cloud_gw(region_name=region)
    client = backend.client('sqs')

    #Get queue URL
    #response = client.get_queue_url(QueueName=queue.url)

   # upload_sequence = None
   # for item in response.get('QueueUrl', []):
 #       if item['QueueUrl'] == settings['message_url']:
    #        upload_sequence = item['uploadSequenceToken']

    with ScheduledEventTracker() as context:
        for resource in matches:
            event = BotEvent('hookpoint', resource, bot.bot_id, bot.name)
            message = jinja2.Template(settings.get('message', ''))
            response = client.send_message(
                QueueUrl=queue.url,
                MessageBody=[{
                    'message': message.render(event=event, resource=resource)
                }],
            )



def load():
    registry.load()
