from rest_framework import serializers

from .models import AccountingExport


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """
    accounting_exports = serializers.SerializerMethodField()

    class Meta:
        model = AccountingExport
        fields = '__all__'

    def get_accounting_exports(self, validated_data):
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')

        accounting_export_type = self.context['request'].parser_context.get('query_params').get('type', None)

        status = self.context['request'].parser_context.get('query_params').get('status', None)

        id = self.context['request'].parser_context.get('query_params').getlist('id')

        start_date = self.context['request'].parser_context.get('query_params').get('start_date', None)

        end_date = self.context['request'].parser_context.get('query_params').get('end_date', None)


        filters = {
            'workspace_id': workspace_id,
            'status__in': ['COMPLETE'],
        }

        if start_date and end_date:
            filters['updated_at__range'] = [start_date, end_date]

        if accounting_export_type:
            filters['type__in'] = accounting_export_type.split(',')

        if id:
            filters['id__in'] = id

        if status:
            filters['status__in'] = status.split(',')

        return AccountingExport.objects.filter(
            **filters
        ).all().order_by("-updated_at")
