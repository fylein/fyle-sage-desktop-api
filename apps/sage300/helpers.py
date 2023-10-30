
from datetime import datetime, timezone
import logging

from django.utils.module_loading import import_string

from apps.workspaces.models import Workspace, Sage300Credential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


# Import your Workspace and Sage300Credential models here
# Also, make sure you have 'logger' defined and imported from a logging module
def check_interval_and_sync_dimension(workspace: Workspace, sage300_credential: Sage300Credential) -> bool:
    """
    Check the synchronization interval and trigger dimension synchronization if needed.

    :param workspace: Workspace Instance
    :param sage300_credential: Sage300Credential Instance

    :return: True if synchronization is triggered, False if not
    """

    if workspace.destination_synced_at:
        # Calculate the time interval since the last destination sync
        time_interval = datetime.now(timezone.utc) - workspace.destination_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        # If destination_synced_at is None or the time interval is greater than 0 days, trigger synchronization
        sync_dimensions(sage300_credential, workspace.id)
        return True

    return False


def sync_dimensions(sage300_credential: Sage300Credential, workspace_id: int) -> None:
    """
    Synchronize various dimensions with Sage 300 using the provided credentials.

    :param sage300_credential: Sage300Credential Instance
    :param workspace_id: ID of the workspace

    This function syncs dimensions like accounts, vendors, commitments, jobs, categories, and cost codes.
    """

    # Initialize the Sage 300 connection using the provided credentials and workspace ID
    sage300_connection = import_string('apps.sage300.utils.SageDesktopConnector')(sage300_credential, workspace_id)

    # List of dimensions to sync
    dimensions = ['accounts', 'vendors', 'commitments', 'jobs', 'standard_categories', 'standard_cost_codes']

    for dimension in dimensions:
        try:
            # Dynamically call the sync method based on the dimension
            sync = getattr(sage300_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            # Log any exceptions that occur during synchronization
            logger.info(exception)
