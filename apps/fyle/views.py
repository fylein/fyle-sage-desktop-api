import logging
from rest_framework import generics
from sage_desktop_api.utils import LookupFieldMixin
from apps.workspaces.models import Workspace
from apps.fyle.serializers import ImportFyleAttributesSerializer, ExpenseFilterSerializer, ExpenseFieldSerializer
from apps.fyle.models import ExpenseFilter

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportFyleAttributesView(generics.CreateAPIView):
    """
    Import Fyle Attributes View
    """

    serializer_class = ImportFyleAttributesSerializer


class ExpenseFilterView(LookupFieldMixin, generics.ListCreateAPIView):
    """
    Expense Filter view
    """

    queryset = ExpenseFilter.objects.all()
    serializer_class = ExpenseFilterSerializer


class ExpenseFilterDeleteView(generics.DestroyAPIView):
    """
    Expense Filter view
    """

    queryset = ExpenseFilter.objects.all()
    serializer_class = ExpenseFilterSerializer


class CustomFieldView(generics.ListAPIView):
    """
    Custom Field view
    """

    serializer_class = ExpenseFieldSerializer
    queryset = Workspace.objects.all()
