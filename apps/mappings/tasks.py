from apps.workspaces.models import Sage300Credential
from apps.sage300.utils import SageDesktopConnector


def sync_sage300_attributes(sage300_attribute_type: str, workspace_id: int):
    sage300_credentials: Sage300Credential = Sage300Credential.objects.get(workspace_id=workspace_id)

    sage300_connection = SageDesktopConnector(
        credentials_object=sage300_credentials,
        workspace_id=workspace_id
    )

    sync_functions = {
        'JOB': sage300_connection.sync_jobs,
        'COST_CODE': sage300_connection.sync_cost_codes,
        'COST_CATEGORY': sage300_connection.sync_cost_categories,
        'ACCOUNT': sage300_connection.sync_accounts,
        'VENDOR': sage300_connection.sync_vendors,
        'COMMITMENT': sage300_connection.sync_commitments,
        'STANDARD_CATEGORY': sage300_connection.sync_standard_categories,
        'STANDARD_COST_CODE': sage300_connection.sync_standard_cost_codes,
    }

    sync_function = sync_functions[sage300_attribute_type]
    sync_function()
