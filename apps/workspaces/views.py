from django.conf import settings

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import status


from apps.workspaces.models import Workspace, Sage300Credentials
from apps.workspaces.serializers import Sage300CredentialSerializer

from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK

class ConnectSageIntacctView(viewsets.ViewSet):
    
    """
    Sage 300 Connect View
    """
    
    def get(self, request, **kwargs):
        """
        Get Sage300 Credentials in Workspace
        """ 
        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            sage300_credentials = Sage300Credentials.objects.get(workspace=workspace)

            return Response(
                data=Sage300CredentialSerializer(sage300_credentials).data,
                status=status.HTTP_200_OK
            )
        except Sage300CredentialSerializer.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct Credentials not found in this workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    def delete(self, request, **kwargs):
        """
        Delete credentials
        """
        workspace_id = kwargs['workspace_id']
        Sage300Credentials.objects.filter(workspace_id=workspace_id).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'message': 'Sage300 credentials deleted'
        })
        
    def post(self, request, **kwargs):
        """
        Post of Sage300 Credentials
        """
        
        sd_username = request.data.get('sd_username')
        sd_user_password = request.data.get('sd_user_password')
        sd_identifier = request.data.get('sd_identifier')
        workspace_id = kwargs['workspace_id']
        workspace = Workspace.objects.get(pk=workspace_id)
        
        sage300_credentials = Sage300Credentials.objects.filter(workspace_id=workspace_id).delete()
        sd_api_key = settings.SD_API_KEY
        sd_api_secret = settings.SD_API_SECRET
        
        SageDesktopSDK(
            api_key=sd_api_key,
            api_secret=sd_api_secret,
            user_name=sd_username,
            password=sd_user_password,
            indentifier=sd_identifier
        )
            
        sage300_credentials = Sage300Credentials.objects.create(
            username=sd_username,
            password=sd_user_password,
            identifier=sd_identifier,
            api_key=sd_api_key,
            api_secret=sd_api_secret
            
        )

        workspace.onboarding_state = 'EXPORT_SETTINGS'
        workspace.save()

        return Response(
            data=Sage300CredentialSerializer(sage300_credentials).data,
            status=status.HTTP_200_OK
        )