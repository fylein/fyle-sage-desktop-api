import logging
from apps.workspaces.models import Workspace
from apps.workspaces.triggers import AdvancedSettingsTriggers

logger = logging.getLogger(__name__)
logger.level = logging.INFO

processed = failed = 0

workspaces = Workspace.objects.filter(onboarding_state='COMPLETE')
for workspace in workspaces:
    try:
        logger.info(f"Processing workspace: {workspace.id} | {workspace.name}")
        AdvancedSettingsTriggers.post_to_integration_settings(workspace.id, True)
        processed += 1
    except Exception as e:
        failed += 1
        logger.error(
            f"Failed to process workspace {workspace.id}: {str(e)}",
            exc_info=True
        )

logger.info(
    f"Completed backfill. Total: {workspaces.count()}\n"
    f"Processed: {processed}, Failed: {failed}"
)
