from unittest import mock
import pytest

from apps.fyle.queue import async_handle_webhook_callback, queue_import_reimbursable_expenses, queue_import_credit_card_expenses
from apps.workspaces.models import Workspace
from tests.test_fyle.fixtures import fixtures as fyle_fixtures
from workers.helpers import RoutingKeyEnum, WorkerActionEnum


@pytest.fixture(autouse=True)
def mock_publish_to_rabbitmq(mocker):
    """Auto-mock publish_to_rabbitmq for all tests in this module"""
    return mocker.patch('apps.fyle.queue.publish_to_rabbitmq')


def test_async_handle_webhook_callback(db, create_temp_workspace, mock_publish_to_rabbitmq):
    """
    Test async_handle_webhook_callback for expense webhooks with RabbitMQ
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

    # Verify RabbitMQ publish was called
    assert mock_publish_to_rabbitmq.called
    call_args = mock_publish_to_rabbitmq.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.EXPENSE_STATE_CHANGE.value
    assert payload['workspace_id'] == 1
    assert call_args[1]['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


def test_async_handle_webhook_callback_direct_export(db, create_temp_workspace, mock_publish_to_rabbitmq):
    """
    Test async_handle_webhook_callback for ACCOUNTING_EXPORT_INITIATED (should be ignored for Sage300)
    """
    body = {
        "action": "ACCOUNTING_EXPORT_INITIATED",
        "data": {
            "id": "rpG6L7AoSHvW",
            "org_id": "riseabovehate1",
            "state": "PAYMENT_PROCESSING"
        }
    }

    async_handle_webhook_callback(body, 1)

    # Should not publish to RabbitMQ for Sage 300 (no direct export)
    mock_publish_to_rabbitmq.assert_not_called()


def test_async_handle_webhook_callback_updated_after_approval(db, create_temp_workspace, mock_publish_to_rabbitmq):
    """
    Test async_handle_webhook_callback for UPDATED_AFTER_APPROVAL
    """
    body = {
        "action": "UPDATED_AFTER_APPROVAL",
        "resource": "EXPENSE",
        "data": {
            "id": "txtest123",
            "org_id": "riseabovehate1"
        }
    }

    async_handle_webhook_callback(body, 1)

    # Verify RabbitMQ publish was called
    assert mock_publish_to_rabbitmq.called
    call_args = mock_publish_to_rabbitmq.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.EXPENSE_UPDATED_AFTER_APPROVAL.value
    assert call_args[1]['routing_key'] == RoutingKeyEnum.UTILITY.value


def test_async_handle_webhook_callback_attribute_webhooks(db, create_temp_workspace, add_feature_config):
    """
    Test async_handle_webhook_callback for attribute webhooks
    """
    from apps.workspaces.models import FeatureConfig
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    body = {
        "action": "CREATED",
        "resource": "CATEGORY",
        "data": {
            "id": "category123",
            "name": "Travel",
            "is_enabled": True,
            "org_id": "riseabovehate1"
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_processor_instance = mock.Mock()
        mock_processor.return_value = mock_processor_instance
        async_handle_webhook_callback(body, 1)
        mock_processor.assert_called_with(1)
        mock_processor_instance.process_webhook.assert_called_with(body)


def test_async_handle_webhook_callback_attribute_webhooks_exception(db, create_temp_workspace, add_feature_config):
    from apps.workspaces.models import FeatureConfig
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    body = {
        "action": "UPDATED",
        "resource": "PROJECT",
        "data": {
            "id": "project123",
            "name": "Project Alpha",
            "org_id": "riseabovehate1"
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_processor.side_effect = Exception("Test exception")
        async_handle_webhook_callback(body, 1)


def test_async_handle_webhook_callback_ejected_from_report(db, create_temp_workspace, mock_publish_to_rabbitmq):
    """
    Test async_handle_webhook_callback for EJECTED_FROM_REPORT action with RabbitMQ
    """
    body = fyle_fixtures['expense_report_change_webhooks']['ejected_from_report']
    workspace = Workspace.objects.get(id=1)

    async_handle_webhook_callback(body, workspace.id)

    # Verify RabbitMQ publish was called
    assert mock_publish_to_rabbitmq.called
    call_args = mock_publish_to_rabbitmq.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.EXPENSE_ADDED_EJECTED_FROM_REPORT.value
    assert call_args[1]['routing_key'] == RoutingKeyEnum.UTILITY.value


def test_async_handle_webhook_callback_added_to_report(db, create_temp_workspace, mock_publish_to_rabbitmq):
    """
    Test async_handle_webhook_callback for ADDED_TO_REPORT action with RabbitMQ
    """
    body = fyle_fixtures['expense_report_change_webhooks']['added_to_report']
    workspace = Workspace.objects.get(id=1)

    async_handle_webhook_callback(body, workspace.id)

    # Verify RabbitMQ publish was called
    assert mock_publish_to_rabbitmq.called
    call_args = mock_publish_to_rabbitmq.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.EXPENSE_ADDED_EJECTED_FROM_REPORT.value
    assert call_args[1]['routing_key'] == RoutingKeyEnum.UTILITY.value


def test_async_handle_webhook_callback_org_setting_updated(db, create_temp_workspace, mock_publish_to_rabbitmq):
    """
    Test async_handle_webhook_callback for ORG_SETTING UPDATED action with RabbitMQ
    """
    body = {
        "action": "UPDATED",
        "resource": "ORG_SETTING",
        "data": {
            "org_id": "riseabovehate1",
            "setting_key": "some_setting"
        }
    }

    async_handle_webhook_callback(body, 1)

    # Verify RabbitMQ publish was called
    assert mock_publish_to_rabbitmq.called
    call_args = mock_publish_to_rabbitmq.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.HANDLE_ORG_SETTING_UPDATED.value
    assert call_args[1]['routing_key'] == RoutingKeyEnum.UTILITY.value


@pytest.mark.django_db
def test_queue_import_reimbursable_expenses_async(mocker, db, create_temp_workspace):
    """
    Test queue_import_reimbursable_expenses publishes to RabbitMQ (asynchronous mode)
    """
    from apps.accounting_exports.models import AccountingExport

    mock_publish = mocker.patch('apps.fyle.queue.publish_to_rabbitmq')

    AccountingExport.objects.create(
        workspace_id=1,
        type='FETCHING_REIMBURSABLE_EXPENSES',
        status='IN_PROGRESS'
    )

    queue_import_reimbursable_expenses(workspace_id=1, synchronous=False)

    # Verify RabbitMQ publish was called
    assert mock_publish.called
    call_args = mock_publish.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.IMPORT_REIMBURSABLE_EXPENSES.value
    assert payload['workspace_id'] == 1
    assert call_args[1]['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


@pytest.mark.django_db
def test_queue_import_credit_card_expenses_async(mocker, db, create_temp_workspace):
    """
    Test queue_import_credit_card_expenses publishes to RabbitMQ (asynchronous mode)
    """
    from apps.accounting_exports.models import AccountingExport

    mock_publish = mocker.patch('apps.fyle.queue.publish_to_rabbitmq')

    AccountingExport.objects.create(
        workspace_id=1,
        type='FETCHING_CREDIT_CARD_EXPENSES',
        status='IN_PROGRESS'
    )

    queue_import_credit_card_expenses(workspace_id=1, synchronous=False)

    # Verify RabbitMQ publish was called
    assert mock_publish.called
    call_args = mock_publish.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.IMPORT_CREDIT_CARD_EXPENSES.value
    assert payload['workspace_id'] == 1
    assert call_args[1]['routing_key'] == RoutingKeyEnum.EXPORT_P1.value
