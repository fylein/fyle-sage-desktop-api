import logging

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.response import Response

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.accounting_exports.serializers import (
    AccountingExportSerializer,
    AccountingExportSummarySerializer,
    ErrorSerializer,
)
from apps.accounting_exports.helpers import AccountingExportSearchFilter

from sage_desktop_api.utils import LookupFieldMixin

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class AccountingExportView(LookupFieldMixin, generics.ListAPIView):
    """
    Retrieve or Create Accounting Export
    """
    serializer_class = AccountingExportSerializer
    queryset = AccountingExport.objects.all().order_by("-updated_at")
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AccountingExportSearchFilter


class AccountingExportCountView(generics.RetrieveAPIView):
    """
    Retrieve Accounting Export Count
    """

    def get(self, request, *args, **kwargs):
        params = {"workspace_id": self.kwargs['workspace_id']}

        if request.query_params.get("status__in"):
            params["status__in"] = request.query_params.get("status__in").split(",")

        return Response({"count": AccountingExport.objects.filter(**params).count()})


class AccountingExportSummaryView(generics.RetrieveAPIView):
    """
    Retrieve Accounting Export Summary
    """
    serializer_class = AccountingExportSummarySerializer
    queryset = AccountingExportSummary.objects.filter(last_exported_at__isnull=False, total_accounting_export_count__gt=0)
    lookup_field = 'workspace_id'

    def get_queryset(self):
        """
        Get queryset
        """
        return super().get_queryset()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve Accounting Export Summary with additional accounting export stats
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = serializer.data

        start_date = request.query_params.get('start_date')
        if start_date:
            accounting_export_stats = AccountingExport.objects.filter(
                workspace_id=instance.workspace_id
            ).aggregate(
                repurposed_successful_count=Count(
                    'id',
                    filter=Q(
                        status='COMPLETE',
                        updated_at__gte=start_date
                    )
                ),
                repurposed_failed_count=Count(
                    'id',
                    filter=Q(status__in=['FAILED', 'FATAL'])
                )
            )

            response.update({
                'repurposed_successful_count': accounting_export_stats['repurposed_successful_count'],
                'repurposed_failed_count': accounting_export_stats['repurposed_failed_count'],
                'repurposed_last_exported_at': start_date
            })

        return Response(response)


class ErrorsView(LookupFieldMixin, generics.ListAPIView):
    serializer_class = ErrorSerializer

    queryset = Error.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {"type": {"exact"}, "is_resolved": {"exact"}}
