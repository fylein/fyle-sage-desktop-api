from rest_framework import serializers

from apps.fyle.helpers import get_expense_fields


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
