from rest_framework import serializers

from .models import AccountingExport, Error, AccountingExportSummary


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """

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

    class Meta:
        model = Error
        fields = '__all__'
