"""
Fyle Serializers
"""
import logging

from django.db.models import Q
from fyle_accounting_mappings.models import ExpenseAttribute
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import status

from apps.fyle.helpers import check_interval_and_sync_dimension, get_expense_fields
from apps.fyle.models import DependentFieldSetting, ExpenseFilter
from apps.mappings.tasks import construct_tasks_and_chain_import_fields_to_fyle
from apps.workspaces.models import FyleCredential

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

            if refresh:
                construct_tasks_and_chain_import_fields_to_fyle(workspace_id=workspace_id)

            check_interval_and_sync_dimension(workspace_id, refresh=True if refresh else False)

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

    field_name = serializers.CharField()
    type = serializers.CharField()
    is_custom = serializers.BooleanField()

    def get_expense_fields(self, workspace_id):
        """
        Get Expense Fields
        """
        expense_fields = get_expense_fields(workspace_id=workspace_id)

        return expense_fields


class FyleFieldsSerializer(serializers.Serializer):
    """
    Fyle Fields Serializer
    """

    attribute_type = serializers.CharField()
    display_name = serializers.CharField()
    is_dependant = serializers.BooleanField()

    def format_fyle_fields(self, workspace_id):
        """
        Get Fyle Fields
        """

        attribute_types = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'TAX_GROUP', 'CORPORATE_CARD', 'MERCHANT']

        attributes = ExpenseAttribute.objects.filter(
            ~Q(attribute_type__in=attribute_types),
            workspace_id=workspace_id
        ).values('attribute_type', 'display_name', 'detail__is_dependent').distinct()

        attributes_list = [
            {'attribute_type': 'COST_CENTER', 'display_name': 'Cost Center', 'is_dependant': False},
            {'attribute_type': 'PROJECT', 'display_name': 'Project', 'is_dependant': False}
        ]

        for attr in attributes:
            attributes_list.append({
                'attribute_type': attr['attribute_type'],
                'display_name': attr['display_name'],
                'is_dependant': attr['detail__is_dependent']
            })

        return attributes_list


class DependentFieldSettingSerializer(serializers.ModelSerializer):
    """
    Dependent Field serializer
    """
    project_field_id = serializers.IntegerField(required=False)
    cost_code_field_id = serializers.IntegerField(required=False)
    category_field_id = serializers.IntegerField(required=False)

    class Meta:
        model = DependentFieldSetting
        fields = '__all__'
