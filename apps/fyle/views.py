from rest_framework import generics

from apps.workspaces.models import Workspace
from apps.fyle.serializers import ExpenseFieldSerializer


class CustomFieldView(generics.ListAPIView):
    """
    Custom Field view
    """

    serializer_class = ExpenseFieldSerializer
    queryset = Workspace.objects.all()
