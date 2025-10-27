"""
Test workspace models
"""
from unittest import mock

from django.core.cache import cache

from apps.workspaces.models import FeatureConfig


def test_feature_config_get_feature_config(db, create_temp_workspace, add_feature_config):
    """
    Test FeatureConfig.get_feature_config method with caching
    """
    workspace_id = 1
    cache.clear()
    result = FeatureConfig.get_feature_config(workspace_id, 'export_via_rabbitmq')
    assert result is True
    result = FeatureConfig.get_feature_config(workspace_id, 'fyle_webhook_sync_enabled')
    assert result is False
    with mock.patch('apps.workspaces.models.FeatureConfig.objects.get') as mock_get:
        result = FeatureConfig.get_feature_config(workspace_id, 'export_via_rabbitmq')
        assert result is True
        mock_get.assert_not_called()

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    cache.clear()
    result = FeatureConfig.get_feature_config(workspace_id, 'fyle_webhook_sync_enabled')
    assert result is True
