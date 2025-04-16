import logging

from rest_framework import generics
from rest_framework.views import Response, status
from django.contrib.auth import get_user_model

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from fyle_rest_auth.utils import AuthUtils

from fyle_accounting_mappings.models import MappingSetting

from fyle_integrations_imports.models import ImportLog

from sage_desktop_api.utils import assert_valid
from apps.workspaces.tasks import export_to_sage300
from apps.workspaces.models import (
    Workspace,
    Sage300Credential,
    ExportSetting,
    AdvancedSetting
)
from apps.workspaces.serializers import (
    WorkspaceSerializer,
    Sage300CredentialSerializer,
    ExportSettingsSerializer,
    ImportSettingsSerializer,
    AdvancedSettingSerializer,
    WorkspaceAdminSerializer
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO

User = get_user_model()
auth_utils = AuthUtils()


class WorkspaceView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Create Retrieve Workspaces
    """
    serializer_class = WorkspaceSerializer

    def get_object(self):
        """
        return workspace object for the given org_id
        """
        user_id = self.request.user

        org_id = self.request.query_params.get('org_id')

        assert_valid(org_id is not None, 'org_id is missing')

        workspace = Workspace.objects.filter(org_id=org_id, user__user_id=user_id).first()

        assert_valid(
            workspace is not None,
            'Workspace not found or the user does not have access to workspaces'
        )

        return workspace


class ReadyView(generics.RetrieveAPIView):
    """
    Ready call to check if the api is ready
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        Ready call
        """
        Workspace.objects.first()

        return Response(
            data={
                'message': 'Ready'
            },
            status=status.HTTP_200_OK
        )


class Sage300CredsView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Sage 300 Creds View
    """
    serializer_class = Sage300CredentialSerializer
    lookup_field = 'workspace_id'

    queryset = Sage300Credential.objects.all()


class ExportSettingView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Retrieve or Create Export Settings
    """
    serializer_class = ExportSettingsSerializer
    lookup_field = 'workspace_id'

    queryset = ExportSetting.objects.all()


class ImportSettingView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or Create Import Settings
    """
    serializer_class = ImportSettingsSerializer

    def get_object(self):
        return Workspace.objects.filter(id=self.kwargs['workspace_id']).first()


class AdvancedSettingView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Retrieve or Create Advanced Settings
    """
    serializer_class = AdvancedSettingSerializer
    lookup_field = 'workspace_id'
    lookup_url_kwarg = 'workspace_id'

    queryset = AdvancedSetting.objects.all()


class WorkspaceAdminsView(generics.ListAPIView):
    """
    Retrieve Workspace Admins
    """
    serializer_class = WorkspaceAdminSerializer
    queryset = Workspace.objects.all()


class TriggerExportsView(generics.GenericAPIView):
    """
    Trigger exports creation
    """

    def post(self, request, *args, **kwargs):
        export_to_sage300(workspace_id=kwargs['workspace_id'], triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC)

        return Response(
            status=status.HTTP_200_OK
        )


class ImportCodeFieldView(generics.GenericAPIView):
    """
    Import Code Field View
    """

    def get(self, request, *args, **kwargs):
        workspace_id = kwargs['workspace_id']

        import_log_attributes = ImportLog.objects.filter(workspace_id=workspace_id).values_list('attribute_type', flat=True)

        response_data = {
            'JOB': True,
            'VENDOR': True,
            'ACCOUNT': True
        }

        project_mapping = MappingSetting.objects.filter(workspace_id=workspace_id, destination_field='JOB').first()

        if project_mapping and project_mapping.source_field in import_log_attributes:
            response_data['JOB'] = False

        if 'MERCHANT' in import_log_attributes:
            response_data['VENDOR'] = False

        if 'CATEGORY' in import_log_attributes:
            response_data['ACCOUNT'] = False

        return Response(
            data=response_data,
            status=status.HTTP_200_OK
        )
