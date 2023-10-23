"""
Fyle Serializers
"""
import logging
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import status
from fyle_integrations_platform_connector import PlatformConnector
from datetime import datetime, timezone
from apps.workspaces.models import Workspace, FyleCredential
from apps.fyle.models import ExpenseFilter


logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportFyleAttributesSerializer(serializers.Serializer):
    """
    Import Fyle Attributes serializer
    """

    def create(self, validated_data):
        """
        Import Fyle Attributes
        """
        try:
            workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
            refresh = self.context['request'].data.get('refresh')

            workspace = Workspace.objects.get(id=workspace_id)
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            platform = PlatformConnector(fyle_credentials)

            if refresh:
                platform.import_fyle_dimensions()
                workspace.source_synced_at = datetime.now()
                workspace.save(update_fields=['source_synced_at'])

            else:
                if workspace.source_synced_at:
                    time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

                if workspace.source_synced_at is None or time_interval.days > 0:
                    platform.import_fyle_dimensions()
                    workspace.source_synced_at = datetime.now()
                    workspace.save(update_fields=['source_synced_at'])

            return Response(status=status.HTTP_200_OK)

        except FyleCredential.DoesNotExist:
            raise serializers.ValidationError({'message': 'Fyle credentials not found in workspace'}, code='invalid_login')

        except Exception as exception:
            logger.error('Something unexpected happened workspace_id: %s %s', workspace_id, exception)
            raise APIException("Internal Server Error", code='server_error')


class ExpenseFilterSerializer(serializers.ModelSerializer):
    """
    Expense Filter Serializer
    """

    class Meta:
        model = ExpenseFilter
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')

        expense_filter, _ = ExpenseFilter.objects.update_or_create(workspace_id=workspace_id, rank=validated_data['rank'], defaults=validated_data)

        return expense_filter
