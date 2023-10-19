import logging
from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.views import Response, status
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from fyle_rest_auth.utils import AuthUtils

from sage_desktop_api.utils import assert_valid
from apps.workspaces.models import (
    Workspace,
    Sage300Credentials,
    ExportSettings
)
from apps.workspaces.serializers import (
    WorkspaceSerializer,
    Sage300CredentialSerializer,
    ExportSettingsSerializer
)

from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK
from sage_desktop_sdk.exceptions import (
    UserAccountLocked, 
    InvalidUserCredentials, 
    InvalidWebApiClientCredentials, 
    WebApiClientLocked
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

    permission_classes = [  # Remove IsAuthenticated once we have a proper auth flow
        IsAuthenticated
    ]

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

    queryset = Sage300Credentials.objects.all()


class ExportSettingView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Retrieve or Create Export Settings
    """
    serializer_class = ExportSettingsSerializer
    lookup_field = 'workspace_id'

    queryset = ExportSettings.objects.all()
