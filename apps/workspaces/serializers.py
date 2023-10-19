"""
Workspace Serializers
"""
from rest_framework import serializers
from django.conf import settings
from django.core.cache import cache
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_rest_auth.models import AuthToken

from apps.fyle.helpers import get_cluster_domain
from sage_desktop_api.utils import assert_valid

from .models import (
    Sage300Credentials,
    ImportSetting,
    AdvancedSetting
)
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK
from sage_desktop_sdk.exceptions import (
    UserAccountLocked,
    InvalidUserCredentials,
    InvalidWebApiClientCredentials,
    WebApiClientLocked
)

from apps.fyle.helpers import get_cluster_domain
from apps.workspaces.models import (
    Workspace,
    FyleCredential,
    Sage300Credentials,
    ExportSettings
)
from apps.users.models import User


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Workspace serializer
    """
    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ('id', 'name', 'org_id', 'created_at', 'updated_at', 'user')

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
    
    api_key = serializers.CharField(required=False)
    api_secret = serializers.CharField(required=False)

    class Meta:
        model = Sage300Credentials
        fields = '__all__'


    def create(self, validated_data):
        try:
            username = validated_data.get('username')
            password = validated_data.get('password')
            identifier = validated_data.get('identifier')
            workspace = validated_data.get('workspace')
            sd_api_key = settings.SD_API_KEY
            sd_api_secret = settings.SD_API_SECRET

            # Initialize SageDesktopSDK or perform necessary actions.
            SageDesktopSDK(
                api_key=sd_api_key,
                api_secret=sd_api_secret,
                user_name=username,
                password=password,
                indentifier=identifier
            )

            # Save the Sage300Credentials instance and update the workspace
            instance = Sage300Credentials.objects.create(
                username=username,
                password=password,
                identifier=identifier,
                api_key=sd_api_key,
                api_secret=sd_api_secret,
                workspace=workspace
            )

            workspace.onboarding_state = 'EXPORT_SETTINGS'
            workspace.save()

            return instance

        except (InvalidUserCredentials, InvalidWebApiClientCredentials, UserAccountLocked, WebApiClientLocked) as e:
            raise serializers.ValidationError(str(e))


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


class ImportSettingsSerializer(serializers.ModelSerializer):
    """
    Export Settings serializer
    """
    class Meta:
        model = ImportSetting
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')
    def create(self, validated_data):
        """
        Create Export Settings
        """
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        import_settings, _ = ImportSetting.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )
        # Update workspace onboarding state
        workspace = import_settings.workspace
        if workspace.onboarding_state == 'IMPORT_SETTINGS':
            workspace.onboarding_state = 'ADVANCED_SETTINGS'
            workspace.save()

        return import_settings


class AdvancedSettingSerializer(serializers.ModelSerializer):
    """
    Advanced Settings serializer
    """
    class Meta:
        model = AdvancedSetting
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create Advanced Settings
        """
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        advanced_setting = AdvancedSetting.objects.filter(
            workspace_id=workspace_id).first()

        if not advanced_setting:
            if 'expense_memo_structure' not in validated_data:
                validated_data['expense_memo_structure'] = [
                    'employee_email',
                    'merchant',
                    'purpose',
                    'report_number'
                ]

        advanced_setting, _ = AdvancedSetting.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        # Update workspace onboarding state
        workspace = advanced_setting.workspace

        if workspace.onboarding_state == 'ADVANCED_SETTINGS':
            workspace.onboarding_state = 'COMPLETE'
            workspace.save()

        return advanced_setting
