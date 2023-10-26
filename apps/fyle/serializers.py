"""
Fyle Serializers
"""
import logging
from django.db.models import Q
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import status
from fyle_integrations_platform_connector import PlatformConnector

from fyle_accounting_mappings.models import ExpenseAttribute

from datetime import datetime, timezone
from apps.workspaces.models import Workspace, FyleCredential
from apps.fyle.models import ExpenseFilter
from apps.fyle.helpers import get_expense_fields


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


class ExpenseFieldSerializer(serializers.Serializer):
    """
    Workspace Admin Serializer
    """
    expense_fields = serializers.SerializerMethodField()

    def get_expense_fields(self, validated_data):
        """
        Get Expense Fields
        """

        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        expense_fields = get_expense_fields(workspace_id=workspace_id)

        return expense_fields


class FyleFieldsSerializer(serializers.Serializer):
    """
    Fyle Fields Serializer
    """

    attribute_type = serializers.CharField()
    display_name = serializers.CharField()

    def format_fyle_fields(self, workspace_id):
        """
        Get Fyle Fields
        """

        default_attributes = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'TAX_GROUP', 'CORPORATE_CARD', 'MERCHANT']

        attributes = ExpenseAttribute.objects.filter(~Q(attribute_type__in=default_attributes), workspace_id=workspace_id, detail__is_dependent=False).values('attribute_type', 'display_name').distinct()

        fyle_fields = [{'attribute_type': 'COST_CENTER', 'display_name': 'Cost Center'}, {'attribute_type': 'PROJECT', 'display_name': 'Project'}]

        for attribute in attributes:
            fyle_fields.append(attribute)

        return fyle_fields
