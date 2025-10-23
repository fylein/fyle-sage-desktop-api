from unittest import mock

from apps.fyle.queue import async_handle_webhook_callback


# This test is just for cov
def test_async_handle_webhook_callback(db, create_temp_workspace):
    """
    Test async_handle_webhook_callback for expense webhooks
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
    body['resource'] = 'EXPENSE'
    async_handle_webhook_callback(body, 1)


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
