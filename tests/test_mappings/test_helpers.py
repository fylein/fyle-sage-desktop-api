from datetime import datetime, timedelta, timezone
from apps.mappings.helpers import prepend_code_to_name, is_job_sync_allowed
from fyle_integrations_imports.models import ImportLog


def test_prepend_code_to_name():
    # Test case 1: use_code_in_naming is True and attribute_code is not None
    result = prepend_code_to_name(True, "attribute_name", "attribute_code")
    assert result == "attribute_code: attribute_name"

    # Test case 2: use_code_in_naming is True but attribute_code is None
    result = prepend_code_to_name(True, "attribute_name", None)
    assert result == "attribute_name"

    # Test case 3: use_code_in_naming is False and attribute_code is not None
    result = prepend_code_to_name(False, "attribute_name", "attribute_code")
    assert result == "attribute_name"

    # Test case 4: use_code_in_naming is False and attribute_code is None
    result = prepend_code_to_name(False, "attribute_name", None)
    assert result == "attribute_name"


def test_is_job_sync_allowed(db, create_temp_workspace):
    import_log = ImportLog.create('PROJECT', 1)

    # Test case 1: import_log is None
    result = is_job_sync_allowed(None)
    assert result is True

    # Test case 2: import_log is not None and last_successful_run_at is None
    import_log.last_successful_run_at = None
    import_log.status = 'COMPLETE'
    result = is_job_sync_allowed(import_log)
    assert result is True

    # Test case 3: import_log is not None and last_successful_run_at is less than 30 minutes
    import_log.last_successful_run_at = (datetime.now(timezone.utc) - timedelta(minutes=29)).replace(tzinfo=timezone.utc)
    import_log.status = 'FATAL'
    result = is_job_sync_allowed(import_log)
    assert result is False

    # Test case 4: import_log is not None and last_successful_run_at is greater than 30 minutes
    import_log.last_successful_run_at = datetime.now(timezone.utc) - timedelta(minutes=31)
    import_log.status = 'COMPLETE'
    result = is_job_sync_allowed(import_log)
    assert result is True
