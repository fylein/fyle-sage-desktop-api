import logging
from rest_framework import generics
from rest_framework.views import status
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from sage_desktop_api.utils import LookupFieldMixin
from apps.fyle.serializers import (
    ImportFyleAttributesSerializer,
    ExpenseFilterSerializer,
    ExpenseFieldSerializer,
    FyleFieldsSerializer,
    DependentFieldSettingSerializer
)
from apps.accounting_exports.serializers import ExpenseSerializer

from apps.accounting_exports.helpers import ExpenseSearchFilter

from apps.workspaces.models import ExportSetting
from apps.fyle.models import ExpenseFilter, DependentFieldSetting, Expense
from apps.fyle.helpers import get_exportable_accounting_exports_ids
from apps.fyle.queue import queue_import_reimbursable_expenses, queue_import_credit_card_expenses

from apps.fyle.exceptions import handle_view_exceptions
from apps.fyle.queue import async_handle_webhook_callback

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
    pagination_class = None

    def get_queryset(self):
        return ExpenseFieldSerializer().get_expense_fields(self.kwargs["workspace_id"])


class FyleFieldsView(generics.ListAPIView):
    """
    Fyle Fields view
    """

    serializer_class = FyleFieldsSerializer
    pagination_class = None

    def get_queryset(self):
        return FyleFieldsSerializer().format_fyle_fields(self.kwargs["workspace_id"])


class DependentFieldSettingView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    """
    Dependent Field view
    """
    serializer_class = DependentFieldSettingSerializer
    lookup_field = 'workspace_id'
    queryset = DependentFieldSetting.objects.all()


class ExportableAccountingExportView(generics.RetrieveAPIView):
    """
    List Exportable Accounting Exports
    """
    def get(self, request, *args, **kwargs):

        exportable_ids = get_exportable_accounting_exports_ids(workspace_id=kwargs['workspace_id'])

        return Response(
            data={'exportable_accounting_export_ids': exportable_ids},
            status=status.HTTP_200_OK
        )


class AccountingExportSyncView(generics.CreateAPIView):
    """
    Create expense groups
    """
    def post(self, request, *args, **kwargs):
        """
        Post expense groups creation
        """

        export_settings = ExportSetting.objects.get(workspace_id=kwargs['workspace_id'])
        if export_settings.reimbursable_expenses_export_type:
            queue_import_reimbursable_expenses(kwargs['workspace_id'], synchronous=True)

        if export_settings.credit_card_expense_export_type:
            queue_import_credit_card_expenses(kwargs['workspace_id'], synchronous=True)

        return Response(
            status=status.HTTP_200_OK
        )


class SkippedExpenseView(generics.ListAPIView):
    """
    List Skipped Expenses
    """
    serializer_class = ExpenseSerializer
    queryset = Expense.objects.all().order_by("-updated_at")
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpenseSearchFilter


class WebhookCallbackView(generics.CreateAPIView):
    """
    Export View
    """
    authentication_classes = []
    permission_classes = []

    @handle_view_exceptions()
    def post(self, request, *args, **kwargs):
        async_handle_webhook_callback(request.data, int(kwargs['workspace_id']))

        return Response(data={}, status=status.HTTP_200_OK)
