from fyle_accounting_mappings.serializers import ExpenseAttributeSerializer
from rest_framework import serializers

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error, Expense


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Expense serializer
    """

    class Meta:
        model = Expense
        fields = ['updated_at', 'claim_number', 'employee_email', 'employee_name', 'fund_source', 'expense_number', 'payment_number', 'vendor', 'category', 'amount', 'report_id', 'expense_id', 'org_id']


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """

    id = serializers.IntegerField()
    expenses = ExpenseSerializer(many=True)

    class Meta:
        model = AccountingExport
        fields = '__all__'


class AccountingExportSummarySerializer(serializers.ModelSerializer):
    """
    Accounting Export Summary serializer
    """
    repurposed_successful_count = serializers.SerializerMethodField()
    repurposed_failed_count = serializers.SerializerMethodField()
    repurposed_last_exported_at = serializers.SerializerMethodField()

    class Meta:
        model = AccountingExportSummary
        fields = '__all__'

    def get_repurposed_successful_count(self, obj):
        """
        Get repurposed successful count based on start_date query parameter
        """
        request = self.context.get('request')

        start_date = request.query_params.get('start_date')
        if not start_date:
            return None

        return AccountingExport.objects.filter(
            workspace_id=obj.workspace_id,
            status='COMPLETE',
            updated_at__gte=start_date,
            type__in=['PURCHASE_INVOICE', 'DIRECT_COST']
        ).count()

    def get_repurposed_failed_count(self, obj):
        """
        Get repurposed failed count based on start_date query parameter
        """
        request = self.context.get('request')

        start_date = request.query_params.get('start_date')
        if not start_date:
            return None

        return AccountingExport.objects.filter(
            workspace_id=obj.workspace_id,
            status__in=['FAILED', 'FATAL'],
            type__in=['PURCHASE_INVOICE', 'DIRECT_COST']
        ).count()

    def get_repurposed_last_exported_at(self, obj):
        """
        Get repurposed last exported at (same as start_date query parameter)
        """
        request = self.context.get('request')

        return request.query_params.get('start_date')


class ErrorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Errors
    """

    accounting_export = AccountingExportSerializer()
    expense_attribute = ExpenseAttributeSerializer()

    class Meta:
        model = Error
        fields = '__all__'
