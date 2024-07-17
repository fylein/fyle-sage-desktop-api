from datetime import datetime, timedelta, timezone
from apps.mappings.helpers import format_attribute_name, allow_job_sync
from apps.mappings.models import ImportLog


def test_format_attribute_name():
    # Test case 1: use_code_in_naming is True and attribute_code is not None
    result = format_attribute_name(True, "attribute_name", "attribute_code")
    assert result == "attribute_code attribute_name"

    # Test case 2: use_code_in_naming is True but attribute_code is None
    result = format_attribute_name(True, "attribute_name", None)
    assert result == "attribute_name"

    # Test case 3: use_code_in_naming is False and attribute_code is not None
    result = format_attribute_name(False, "attribute_name", "attribute_code")
    assert result == "attribute_name"

    # Test case 4: use_code_in_naming is False and attribute_code is None
    result = format_attribute_name(False, "attribute_name", None)
    assert result == "attribute_name"


def test_allow_job_sync(db, create_temp_workspace):
    import_log = ImportLog.create('PROJECT', 1)

    # Test case 1: import_log is None
    result = allow_job_sync(None)
    assert result is True

    # Test case 2: import_log is not None and last_successful_run_at is None
    import_log.last_successful_run_at = None
    import_log.status = 'COMPLETE'
    result = allow_job_sync(import_log)
    assert result is True

    # Test case 3: import_log is not None and status is not 'COMPLETE'
    import_log.last_successful_run_at = '2021-01-01T00:00:00Z'
    import_log.status = 'FATAL'
    result = allow_job_sync(import_log)
    assert result is True

    # Test case 4: import_log is not None and last_successful_run_at is less than 30 minutes
    import_log.last_successful_run_at = datetime.now(timezone.utc) - timedelta(minutes=29)
    import_log.status = 'COMPLETE'
    result = allow_job_sync(import_log)
    assert result is False

    # Test case 5: import_log is not None and last_successful_run_at is greater than 30 minutes
    import_log.last_successful_run_at = datetime.now(timezone.utc) - timedelta(minutes=31)
    import_log.status = 'COMPLETE'
    result = allow_job_sync(import_log)
    assert result is True
