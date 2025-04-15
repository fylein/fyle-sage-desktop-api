from fyle_integrations_platform_connector import PlatformConnector

from fyle_integrations_imports.modules.base import Base
from apps.workspaces.models import FyleCredential


def get_base_class_instance(
    workspace_id: int = 1,
    source_field: str = "COST_CENTER",
    destination_field: str = "COST_CENTER",
    platform_class_name: str = "cost_centers",
    sync_after: str = None,
    destination_sync_methods: list = None,
    sdk_connection: str = 'sdk_connection'
):

    base = Base(
        workspace_id=workspace_id,
        source_field=source_field,
        destination_field=destination_field,
        platform_class_name=platform_class_name,
        sync_after=sync_after,
        sdk_connection=sdk_connection,
        destination_sync_methods=destination_sync_methods
    )

    return base


def get_platform_connection(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    return platform
