import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from sage_desktop_api.utils import LookupFieldMixin
from apps.accounting_exports.serializers import AccountingExportSerializer
from apps.accounting_exports.models import AccountingExport

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
