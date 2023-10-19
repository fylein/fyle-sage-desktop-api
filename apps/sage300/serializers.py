import logging
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import status

from datetime import datetime, timezone
from apps.workspaces.models import Workspace, Sage300Credentials
from apps.sage300.helpers import sync_dimensions, check_interval_and_sync_dimension

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSage300AttributesSerializer(serializers.Serializer):
    """
    Import Sage300 Attributes serializer
    """

    def create(self, validated_data):

        try:
            workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
            refresh_dimension = self.context['request'].data.get('refresh')

            workspace = Workspace.objects.get(pk=workspace_id)
            sage_intacct_credentials = Sage300Credentials.objects.get(workspace_id=workspace.id)

            if refresh_dimension:
                synced = True
                sync_dimensions(sage_intacct_credentials, workspace.id)
            else:
                synced = check_interval_and_sync_dimension(workspace, sage_intacct_credentials)

            if synced:
                workspace.destination_synced_at = datetime.now()
                workspace.save(update_fields=['destination_synced_at'])

            return Response(
                status=status.HTTP_200_OK
            )

        except Sage300Credentials.DoesNotExist:
            raise serializers.ValidationError({'message': 'Sage300 credentials not found / invalid in workspace'})

        except Exception as exception:
            logger.error('Something unexpected happened workspace_id: %s %s', workspace_id, exception)
            raise serializers.ValidationError()
