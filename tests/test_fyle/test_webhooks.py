"""
Test Fyle webhook attribute processing
"""
from unittest import mock

import pytest
from django.core.cache import cache

from apps.fyle.queue import async_handle_webhook_callback
from apps.workspaces.models import FeatureConfig


@pytest.mark.django_db
def test_webhook_attribute_processing_category_created(db, create_temp_workspace, add_feature_config):
    """Test processing CATEGORY CREATED webhook"""
    cache.clear()
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    webhook_body = {
        'action': 'CREATED',
        'resource': 'CATEGORY',
        'data': {
            'id': 'cat_123',
            'name': 'Travel',
            'sub_category': 'Flight',
            'is_enabled': True,
            'org_id': 'riseabovehate1'
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_instance = mock.Mock()
        mock_processor.return_value = mock_instance
        async_handle_webhook_callback(webhook_body, 1)
        mock_processor.assert_called_once_with(1)
        mock_instance.process_webhook.assert_called_once_with(webhook_body)


@pytest.mark.django_db
def test_webhook_attribute_processing_project_created(db, create_temp_workspace, add_feature_config):
    """Test processing PROJECT webhook"""
    cache.clear()
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    webhook_body = {
        'action': 'CREATED',
        'resource': 'PROJECT',
        'data': {
            'id': 'proj_123',
            'name': 'Main Project',
            'sub_project': 'Sub Project 1',
            'is_enabled': True,
            'org_id': 'riseabovehate1'
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_instance = mock.Mock()
        mock_processor.return_value = mock_instance
        async_handle_webhook_callback(webhook_body, 1)
        mock_processor.assert_called_once_with(1)
        mock_instance.process_webhook.assert_called_once_with(webhook_body)


@pytest.mark.django_db
def test_webhook_attribute_processing_category_deleted(db, create_temp_workspace, add_feature_config):
    """Test processing CATEGORY DELETED webhook"""
    cache.clear()
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    webhook_body = {
        'action': 'DELETED',
        'resource': 'CATEGORY',
        'data': {
            'id': 'cat_789',
            'name': 'Old Category',
            'org_id': 'riseabovehate1'
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_instance = mock.Mock()
        mock_processor.return_value = mock_instance
        async_handle_webhook_callback(webhook_body, 1)
        mock_processor.assert_called_once_with(1)
        mock_instance.process_webhook.assert_called_once_with(webhook_body)


@pytest.mark.django_db
def test_webhook_attribute_processing_employee(db, create_temp_workspace, add_feature_config):
    """Test processing EMPLOYEE webhook"""
    cache.clear()
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()

    webhook_body = {
        'action': 'CREATED',
        'resource': 'EMPLOYEE',
        'data': {
            'id': 'emp_123',
            'user': {
                'email': 'employee@example.com',
                'full_name': 'John Doe'
            },
            'user_id': 'user_123',
            'code': 'EMP001',
            'is_enabled': True,
            'org_id': 'riseabovehate1'
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_instance = mock.Mock()
        mock_processor.return_value = mock_instance
        async_handle_webhook_callback(webhook_body, 1)
        mock_processor.assert_called_once_with(1)
        mock_instance.process_webhook.assert_called_once_with(webhook_body)


@pytest.mark.django_db
def test_webhook_attribute_processing_cost_center(db, create_temp_workspace, add_feature_config):
    """Test processing COST_CENTER webhook"""
    cache.clear()
    feature_config = FeatureConfig.objects.get(workspace_id=1)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()

    webhook_body = {
        'action': 'DELETED',
        'resource': 'COST_CENTER',
        'data': {
            'id': 'cc_delete',
            'name': 'To Be Deleted',
            'org_id': 'riseabovehate1'
        }
    }

    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        mock_instance = mock.Mock()
        mock_processor.return_value = mock_instance
        async_handle_webhook_callback(webhook_body, 1)
        mock_processor.assert_called_once_with(1)
        mock_instance.process_webhook.assert_called_once_with(webhook_body)


@pytest.mark.django_db
def test_webhook_attribute_processing_when_disabled(db, create_temp_workspace, add_feature_config):
    """Test that webhook processing is skipped when feature flag is disabled"""
    cache.clear()
    webhook_body = {
        'action': 'CREATED',
        'resource': 'CATEGORY',
        'data': {
            'id': 'cat_skip',
            'name': 'Should Skip',
            'is_enabled': True,
            'org_id': 'riseabovehate1'
        }
    }
    with mock.patch('apps.fyle.queue.WebhookAttributeProcessor') as mock_processor:
        async_handle_webhook_callback(webhook_body, 1)
        mock_processor.assert_not_called()
