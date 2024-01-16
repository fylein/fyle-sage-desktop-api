from rest_framework import serializers
from fyle_accounting_mappings.serializers import ExpenseAttributeSerializer
from .models import AccountingExport, Error, AccountingExportSummary, Expense


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Expense serializer
    """

    class Meta:
        model = Expense
        fields = ['updated_at', 'claim_number', 'employee_email', 'employee_name', 'fund_source', 'expense_number', 'payment_number', 'vendor', 'category', 'amount', 'report_id', 'settlement_id', 'expense_id', 'org_id']


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """

    expenses = ExpenseSerializer(many=True)

    class Meta:
        model = AccountingExport
        fields = '__all__'


class AccountingExportSummarySerializer(serializers.ModelSerializer):
    """
    Accounting Export Summary serializer
    """

    class Meta:
        model = AccountingExportSummary
        fields = '__all__'


class ErrorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Errors
    """

    expense_attribute = ExpenseAttributeSerializer()

    class Meta:
        model = Error
        fields = '__all__'
