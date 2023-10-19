
from datetime import datetime, timezone
import logging

from django.utils.module_loading import import_string

from apps.workspaces.models import Workspace, Sage300Credentials
from apps.sage300.utils import SageDesktopConnector

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def check_interval_and_sync_dimension(workspace: Workspace, sage300_credential: Sage300Credentials) -> bool:
    """
    Check sync interval and sync dimensions
    :param workspace: Workspace Instance
    :param si_credentials: SageIntacctCredentials Instance

    return: True/False based on sync
    """

    if workspace.destination_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        sync_dimensions(sage300_credential, workspace.id)
        return True

    return False


def sync_dimensions(sage300_credential: Sage300Credentials, workspace_id: int) -> None:
    sage300_connection = import_string(
        'apps.sage300.utils.SageDesktopConnector'
    )(sage300_credential, workspace_id)

    dimensions = [
        'accounts', 'vendors', 'commitments',
        'jobs', 'categories', 'cost_codes'
    ]

    for dimension in dimensions:
        try:
            sync = getattr(sage300_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            logger.info(exception)
