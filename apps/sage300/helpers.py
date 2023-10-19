
from datetime import datetime, timezone
import logging

from django.utils.module_loading import import_string

from apps.workspaces.models import Workspace, Sage300Credentials
from apps.sage300.utils import SageDesktopConnector

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def check_interval_and_sync_dimension(workspace: Workspace, sage300_credentials: Sage300Credentials) -> bool:
    """
    Check sync interval and sync dimensions
    :param workspace: Workspace Instance
    :param si_credentials: SageIntacctCredentials Instance

    return: True/False based on sync
    """

    if workspace.destination_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        sync_dimensions(sage300_credentials, workspace.id)
        return True

    return False



def sync_dimensions(sage300_credentials: Sage300Credentials, workspace_id: int) -> None:

    sage_intacct_connection = SageDesktopConnector(sage300_credentials, workspace_id)

    sage_intacct_connection.sync_accounts()
    return []
