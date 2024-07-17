from datetime import datetime, timedelta, timezone
from apps.mappings.models import ImportLog


def format_attribute_name(use_code_in_naming: bool, attribute_name: str, attribute_code: str = None) -> str:
    """
    Format the attribute name based on the use_code_in_naming flag
    """
    if use_code_in_naming and attribute_code:
        return "{} {}".format(attribute_code, attribute_name)
    return attribute_name


def is_job_sync_allowed(import_log: ImportLog = None) -> bool:
    """
    Check if job sync is allowed
    """
    time_difference = datetime.now(timezone.utc) - timedelta(minutes=30)

    if (
        not import_log
        or import_log.status != 'COMPLETE'
        or import_log.last_successful_run_at is None
        or import_log.last_successful_run_at < time_difference
    ):
        return True

    return False
