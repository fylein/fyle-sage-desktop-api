from apps.workspaces.models import Sage300Credential
from apps.sage300.utils import SageDesktopConnector


def sync_sage300_attributes(sage300_attribute_type: str, workspace_id: int):
    sage300_credentials: Sage300Credential = Sage300Credential.objects.get(workspace_id=workspace_id)

    sage300_connection = SageDesktopConnector(
        credentials_object=sage300_credentials,
        workspace_id=workspace_id
    )

    if sage300_attribute_type == 'JOB':
        sage300_connection.sync_jobs()

    elif sage300_attribute_type == 'COST_CODE':
        sage300_connection.sync_cost_codes()

    elif sage300_attribute_type == 'CATEGORY':
        sage300_connection.sync_categories()

    elif sage300_attribute_type == 'VENDOR':
        sage300_connection.sync_vendors()

    elif sage300_attribute_type == 'COMMITMENT':
        sage300_connection.sync_commitments()

    elif sage300_attribute_type == 'STANDARD_CATEGORY':
        sage300_connection.sync_standard_categories()

    elif sage300_attribute_type == 'STANDARD_COST_CODE':
        sage300_connection.sync_standard_cost_codes()
