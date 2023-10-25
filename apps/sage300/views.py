import logging

from rest_framework import generics

from fyle_accounting_mappings.models import DestinationAttribute

from apps.sage300.serializers import Sage300FieldSerializer
from apps.sage300.serializers import ImportSage300AttributesSerializer


logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSage300AttributesView(generics.CreateAPIView):
    """
    Import Sage300 Attributes View
    """
    serializer_class = ImportSage300AttributesSerializer


class Sage300FieldsView(generics.ListAPIView):
    """
    Sage300 Expense Fields View
    """
    serializer_class = Sage300FieldSerializer

    def get_queryset(self):
        return Sage300FieldSerializer().format_sage300_fields(self.kwargs["workspace_id"])
