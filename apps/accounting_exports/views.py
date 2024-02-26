import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.response import Response

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.accounting_exports.serializers import (
    AccountingExportSerializer,
    AccountingExportSummarySerializer,
    ErrorSerializer,
)
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
    filterset_fields = {"type": {"in"}, "updated_at": {"lte", "gte"}, "id": {"in"}, "status": {"in"}}


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
    lookup_field = 'workspace_id'
    lookup_url_kwarg = 'workspace_id'

    queryset = AccountingExportSummary.objects.filter(last_exported_at__isnull=False, total_accounting_export_count__gt=0)
    serializer_class = AccountingExportSummarySerializer


class ErrorsView(LookupFieldMixin, generics.ListAPIView):
    serializer_class = ErrorSerializer

    queryset = Error.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {"type": {"exact"}, "is_resolved": {"exact"}}
