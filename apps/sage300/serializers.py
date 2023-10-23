import logging
from datetime import datetime
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import status

from fyle_accounting_mappings.models import DestinationAttribute

from apps.workspaces.models import Workspace, Sage300Credential
from apps.sage300.helpers import sync_dimensions, check_interval_and_sync_dimension


logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSage300AttributesSerializer(serializers.Serializer):
    """
    Import Sage300 Attributes serializer
    """

    def create(self, validated_data):
        try:
            # Get the workspace ID from the URL kwargs
            workspace_id = self.context['request'].parser_context['kwargs']['workspace_id']

            # Check if the 'refresh' field is provided in the request data
            refresh_dimension = self.context['request'].data.get('refresh', False)

            # Retrieve the workspace and Sage 300 credentials
            workspace = Workspace.objects.get(pk=workspace_id)
            sage_intacct_credentials = Sage300Credential.objects.get(
                workspace_id=workspace.id
            )

            if refresh_dimension:
                # If 'refresh' is true, perform a full sync of dimensions
                sync_dimensions(sage_intacct_credentials, workspace.id)
            else:
                # If 'refresh' is false, check the interval and sync dimension accordingly
                check_interval_and_sync_dimension(workspace, sage_intacct_credentials)

            # Update the destination_synced_at field and save the workspace
            workspace.destination_synced_at = datetime.now()
            workspace.save(update_fields=['destination_synced_at'])

            # Return a success response
            return Response(status=status.HTTP_200_OK)

        except Sage300Credential.DoesNotExist:
            # Handle the case when Sage 300 credentials are not found or invalid
            raise serializers.ValidationError(
                {'message': 'Sage300 credentials not found / invalid in workspace'}
            )

        except Exception as exception:
            # Handle unexpected exceptions and log the error
            logger.error(
                'Something unexpected happened workspace_id: %s %s',
                workspace_id,
                exception,
            )
            # Raise a custom exception or re-raise the original exception
            raise


class Sage300FieldSerializer(serializers.ModelSerializer):
    """
    Expense Fields Serializer
    """

    class Meta:
        model = DestinationAttribute
        fields = ['attribute_type', 'display_name']
