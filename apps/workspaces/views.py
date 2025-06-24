import logging

from rest_framework import generics
from rest_framework.views import Response, status
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from fyle_rest_auth.utils import AuthUtils

from fyle_accounting_mappings.models import MappingSetting

from fyle_integrations_imports.models import ImportLog

from apps.sage300.utils import SageDesktopConnector
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK

from sage_desktop_api.utils import assert_valid, invalidate_sage300_credentials
from apps.workspaces.tasks import export_to_sage300, patch_integration_settings
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
    permission_classes = []
    pagination_class = None

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

    def post(self, request, **kwargs):
        try:
            identifier = request.data.get('identifier')
            username = request.data.get('username')
            password = request.data.get('password')

            api_key = settings.SD_API_KEY
            api_secret = settings.SD_API_SECRET

            if identifier.startswith('https://'):
                identifier = identifier[8:]
            elif identifier.startswith('http://'):
                identifier = identifier[7:]

            if not identifier.endswith('.hh2.com'):
                identifier = identifier + '.hh2.com'

            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])

            sage300_credentials = Sage300Credential.objects.filter(workspace=workspace).first()

            try:
                sage_300_connection = SageDesktopSDK(
                    api_key=api_key,
                    api_secret=api_secret,
                    user_name=username,
                    password=password,
                    identifier=identifier
                )
                vendors = sage_300_connection.vendors
                vendors.get_vendor_types()
            except Exception as connection_error:
                error_message = str(connection_error)
                logger.error(error_message)
                return Response(
                    {
                        'message': 'Sage300 credentails invalid'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not sage300_credentials:
                sage300_credentials = Sage300Credential.objects.create(
                    identifier=identifier,
                    username=username,
                    password=password,
                    api_key=api_key,
                    api_secret=api_secret,
                    workspace=workspace
                )
                workspace.onboarding_state = 'EXPORT_SETTINGS'
                workspace.save()
            else:
                sage300_credentials.identifier = identifier
                sage300_credentials.username = username
                sage300_credentials.password = password
                sage300_credentials.api_key = api_key
                sage300_credentials.api_secret = api_secret
                sage300_credentials.is_expired = False
                sage300_credentials.save()

                patch_integration_settings(kwargs['workspace_id'], is_token_expired=False)

            return Response(
                data=Sage300CredentialSerializer(sage300_credentials).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.info(e)
            return Response(
                {
                    'message': 'Invalid Login Attempt'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


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


class TokenHealthView(generics.RetrieveAPIView):
    """
    Token Health View
    """

    def get(self, request, *args, **kwargs):
        status_code = status.HTTP_200_OK
        message = "Sage300 connection is active"

        workspace_id = kwargs.get('workspace_id')
        sage300_credentials = Sage300Credential.objects.filter(workspace=workspace_id).first()

        if not sage300_credentials:
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Sage300 credentials not found"
        elif sage300_credentials.is_expired:
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Sage300 connection expired"
        else:
            try:
                cache_key = f'HEALTH_CHECK_CACHE_{workspace_id}'
                is_healthy = cache.get(cache_key)

                if is_healthy is None:
                    sage300_connection = SageDesktopConnector(credentials_object=sage300_credentials, workspace_id=workspace_id)
                    sage300_connection.connection.vendors.get_vendor_types()
                    cache.set(cache_key, True, timeout=timedelta(hours=24).total_seconds())
            except Exception:
                invalidate_sage300_credentials(workspace_id, sage300_credentials)
                status_code = status.HTTP_400_BAD_REQUEST
                message = "Sage300 connection expired"

        return Response({"message": message}, status=status_code)
