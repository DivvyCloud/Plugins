
from DivvyDb import DivvyDbObjects
from DivvyDb.DivvyCloudGatewayORM import DivvyCloudGatewayORM
from DivvyDb.QueryFilters.cloud_types import CloudType
from DivvyDb.QueryFilters.registry import QueryRegistry
from DivvyResource import ResourceType
from DivvyUtils.field_definition import SelectionField, FieldOptions

default_filters_author = 'Fidelity'


@QueryRegistry.register(
    query_id='fidelity.filter.xray_encryption_configuration_type',
    name='X-Ray Encryption Config Types',
    description=(
        'Returns the encryption configuration type used (default, KMS)'
    ),
    author=default_filters_author,
    supported_resources=[ResourceType.SERVICE_REGION],
    supported_clouds=[
        CloudType.AMAZON_WEB_SERVICES,
        CloudType.AMAZON_WEB_SERVICES_GOV
    ],
    settings_config=[
        SelectionField(
            name='type',
            choices=[('NONE', 'Default'), ('KMS', 'KMS')],
            display_name='Encryption Configuration Type',
            description='The type used for the encryption configuration',
            options=[FieldOptions.REQUIRED]
        )
    ],
    version='18.7'
)
def xray_encryption_configuration_type(query, db_cls, settings_config):
    db = DivvyCloudGatewayORM()
    return query.filter(db_cls.resource_id.in_(
        db.session.query(
            DivvyDbObjects.ResourceProperty.resource_id
        ).filter(
            DivvyDbObjects.ResourceProperty.name == 'fidelity.xray_encryption_config_type'
        ).filter(
            DivvyDbObjects.ResourceProperty.value == settings_config['type']
        )))


def load():
    pass
