from rest_framework.views import status
from rest_framework import generics
from rest_framework.response import Response

from fyle_integrations_platform_connector import PlatformConnector

from apps.workspaces.models import FyleCredential
from apps.fyle.constants import DEFAULT_FYLE_CONDITIONS


class CustomFieldView(generics.RetrieveAPIView):
    """
    Custom Field view
    """
    def get(self, request, *args, **kwargs):
        """
        Get Custom Fields
        """
        workspace_id = self.kwargs['workspace_id']

        fyle_credentails = FyleCredential.objects.get(workspace_id=workspace_id)

        platform = PlatformConnector(fyle_credentails)

        custom_fields = platform.expense_custom_fields.list_all()

        response = []
        response.extend(DEFAULT_FYLE_CONDITIONS)
        for custom_field in custom_fields:
            if custom_field['type'] in ('SELECT', 'NUMBER', 'TEXT', 'BOOLEAN'):
                response.append({
                    'field_name': custom_field['field_name'],
                    'type': custom_field['type'],
                    'is_custom': custom_field['is_custom']
                })

        return Response(
            data=response,
            status=status.HTTP_200_OK
        )
