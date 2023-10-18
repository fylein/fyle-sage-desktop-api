from rest_framework import generics

from apps.workspaces.models import (
    Workspace,
    Sage300Credentials
)
from apps.workspaces.serializers import Sage300CredentialSerializer


class Sage300CredsView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Sage 300 Creds View
    """
    serializer_class = Sage300CredentialSerializer
    lookup_field = 'workspace_id'

    queryset = Sage300Credentials.objects.all()
