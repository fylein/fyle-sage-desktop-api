import logging
from rest_framework import generics
from rest_framework.views import status
from rest_framework.response import Response

from sage_desktop_api.utils import LookupFieldMixin
from apps.workspaces.models import Workspace
from apps.fyle.serializers import (
    ImportFyleAttributesSerializer,
    ExpenseFilterSerializer,
    ExpenseFieldSerializer,
    FyleFieldsSerializer,
    DependentFieldSettingSerializer
)
from apps.fyle.models import ExpenseFilter, DependentFieldSetting
from apps.fyle.helpers import get_exportable_accounting_exports_ids


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


class FyleFieldsView(generics.ListAPIView):
    """
    Fyle Fields view
    """

    serializer_class = FyleFieldsSerializer

    def get_queryset(self):
        return FyleFieldsSerializer().format_fyle_fields(self.kwargs["workspace_id"])


class DependentFieldSettingView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    """
    Dependent Field view
    """
    authentication_classes = []
    permission_classes = []
    serializer_class = DependentFieldSettingSerializer
    lookup_field = 'workspace_id'
    queryset = DependentFieldSetting.objects.all()


class ExportableExpenseGroupsView(generics.RetrieveAPIView):
    """
    List Exportable Expense Groups
    """
    def get(self, request, *args, **kwargs):

        exportable_ids = get_exportable_accounting_exports_ids(workspace_id=kwargs['workspace_id'])

        return Response(
            data={'exportable_expense_group_ids': exportable_ids},
            status=status.HTTP_200_OK
        )
