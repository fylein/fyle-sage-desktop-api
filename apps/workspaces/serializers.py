"""
Workspace Serializers
"""
from rest_framework import serializers

from django.core.cache import cache
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_rest_auth.models import AuthToken

from apps.fyle.helpers import get_cluster_domain
from sage_desktop_api.utils import assert_valid

from .models import (
    User,
    Workspace,
    FyleCredential,
    Sage300Credentials,
    ExportSettings
)


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Workspace serializer
    """
    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ('id', 'name', 'org_id', 'fyle_currency', 'created_at', 'updated_at', 'user')

    def create(self, validated_data):
        """
        Update workspace
        """
        access_token = self.context['request'].META.get('HTTP_AUTHORIZATION')
        user = self.context['request'].user

        # Getting user profile using the access token
        fyle_user = get_fyle_admin(access_token.split(' ')[1], None)

        # getting name, org_id, currency of Fyle User
        name = fyle_user['data']['org']['name']
        org_id = fyle_user['data']['org']['id']
        fyle_currency = fyle_user['data']['org']['currency']

        # Checking if workspace already exists
        workspace = Workspace.objects.filter(org_id=org_id).first()

        if workspace:
            # Adding user relation to workspace
            workspace.user.add(User.objects.get(user_id=user))
            cache.delete(str(workspace.id))
        else:
            workspace = Workspace.objects.create(
                name=name,
                org_id=org_id,
                fyle_currency=fyle_currency
            )

            workspace.user.add(User.objects.get(user_id=user))

            auth_tokens = AuthToken.objects.get(user__user_id=user)

            cluster_domain = get_cluster_domain(auth_tokens.refresh_token)

            FyleCredential.objects.update_or_create(
                refresh_token=auth_tokens.refresh_token,
                workspace_id=workspace.id,
                cluster_domain=cluster_domain
            )

        return workspace


class Sage300CredentialSerializer(serializers.ModelSerializer):
    """
    Sage300 credential serializer
    """
    class Meta:
        model = Sage300Credentials
        fields = '__all__'


class ExportSettingsSerializer(serializers.ModelSerializer):
    """
    Export Settings serializer
    """
    class Meta:
        model = ExportSettings
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create Export Settings
        """
        assert_valid(validated_data, 'Body cannot be null')
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')

        export_settings = ExportSettings.objects.filter(
            workspace_id=workspace_id).first()

        export_settings, _ = ExportSettings.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        # Update workspace onboarding state
        workspace = export_settings.workspace

        if workspace.onboarding_state == 'EXPORT_SETTINGS':
            workspace.onboarding_state = 'IMPORT_SETTINGS'
            workspace.save()

        return export_settings
