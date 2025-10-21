from unittest.mock import patch
from apps.fyle.queue import async_handle_webhook_callback
from apps.workspaces.models import Workspace
from tests.test_fyle.fixtures import fixtures as fyle_fixtures


# This test is just for cov
def test_async_handle_webhook_callback(db, create_temp_workspace):
    """
    Test async_handle_webhook_callback
    """
    body = {
        "action": "ADMIN_APPROVED",
        "data": {
            "id": "rpG6L7AoSHvW",
            "org_id": "riseabovehate1",
            "state": "PAYMENT_PROCESSING"
        }
    }

    async_handle_webhook_callback(body, 1)

    body['action'] = 'ACCOUNTING_EXPORT_INITIATED'
    async_handle_webhook_callback(body, 1)

    body['action'] = 'UPDATED_AFTER_APPROVAL'
    async_handle_webhook_callback(body, 1)


@patch('apps.fyle.queue.async_task')
def test_async_handle_webhook_callback_ejected_from_report(mock_async_task, db, create_temp_workspace):
    """
    Test async_handle_webhook_callback for EJECTED_FROM_REPORT action
    """
    body = fyle_fixtures['expense_report_change_webhooks']['ejected_from_report']
    workspace = Workspace.objects.get(id=1)

    async_handle_webhook_callback(body, workspace.id)

    mock_async_task.assert_called_once_with(
        'apps.fyle.tasks.handle_expense_report_change',
        body['data'],
        'EJECTED_FROM_REPORT'
    )


@patch('apps.fyle.queue.async_task')
def test_async_handle_webhook_callback_added_to_report(mock_async_task, db, create_temp_workspace):
    """
    Test async_handle_webhook_callback for ADDED_TO_REPORT action
    """
    body = fyle_fixtures['expense_report_change_webhooks']['added_to_report']
    workspace = Workspace.objects.get(id=1)

    async_handle_webhook_callback(body, workspace.id)

    mock_async_task.assert_called_once_with(
        'apps.fyle.tasks.handle_expense_report_change',
        body['data'],
        'ADDED_TO_REPORT'
    )
