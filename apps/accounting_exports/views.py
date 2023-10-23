import logging
from rest_framework import generics
from sage_desktop_api.utils import LookupFieldMixin
from apps.accounting_exports.serializers import AccountingExportSerializer
from apps.accounting_exports.models import AccountingExport

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class AccountingExportView(generics.ListAPIView):
    """
    Retrieve or Create Accounting Export
    """
    serializer_class = AccountingExportSerializer
    queryset = AccountingExport.objects.all()
