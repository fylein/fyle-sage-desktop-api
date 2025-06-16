import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django_q.tasks import async_task
from fyle_accounting_mappings.models import ExpenseAttribute, MappingSetting
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_rest_auth.models import AuthToken
from rest_framework import serializers

from apps.accounting_exports.models import AccountingExportSummary
from apps.fyle.helpers import get_cluster_domain
from apps.fyle.models import DependentFieldSetting
from apps.mappings.models import Version
from apps.users.models import User
from apps.workspaces.models import (
    AdvancedSetting,
    ExportSetting,
    FyleCredential,
    ImportSetting,
    Sage300Credential,
    Workspace,
)
from apps.workspaces.triggers import AdvancedSettingsTriggers, ImportSettingsTrigger
from fyle_integrations_imports.models import ImportLog
from sage_desktop_api.utils import assert_valid
from sage_desktop_sdk.exceptions import (
    InvalidUserCredentials,
    InvalidWebApiClientCredentials,
    UserAccountLocked,
    WebApiClientLocked,
)
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK

logger = logging.getLogger(__name__)
logger.level = logging.INFO


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
            Version.objects.create(workspace_id=workspace.id)

            workspace.user.add(User.objects.get(user_id=user))

            auth_tokens = AuthToken.objects.get(user__user_id=user)

            cluster_domain = get_cluster_domain(auth_tokens.refresh_token)

            AccountingExportSummary.objects.create(workspace_id=workspace.id)

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
        model = Sage300Credential
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

            # Save the Sage300Credential instance and update the workspace
            instance = Sage300Credential.objects.create(
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
        model = ExportSetting
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create Export Settings
        """
        assert_valid(validated_data, 'Body cannot be null')
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')

        export_settings, _ = ExportSetting.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        # Update workspace onboarding state
        workspace = export_settings.workspace

        if export_settings.credit_card_expense_export_type == 'PURCHASE_INVOICE':
            MappingSetting.objects.update_or_create(
                workspace_id = workspace_id,
                destination_field='VENDOR',
                defaults={
                    'source_field':'CORPORATE_CARD',
                    'import_to_fyle': False,
                    'is_custom': False
                }
            )

        if workspace.onboarding_state == 'EXPORT_SETTINGS':
            workspace.onboarding_state = 'IMPORT_SETTINGS'
            workspace.save()

        return export_settings


class MappingSettingFilteredListSerializer(serializers.ListSerializer):
    """
    Serializer to filter the active system, which is a boolen field in
    System Model. The value argument to to_representation() method is
    the model instance
    """
    def to_representation(self, data):
        data = data.filter(~Q(
            destination_field__in=[
                'ACCOUNT',
                'CCC_ACCOUNT',
                'CHARGE_CARD_NUMBER',
                'EMPLOYEE',
                'EXPENSE_TYPE',
                'TAX_DETAIL',
                'VENDOR'
            ])
        )
        return super(MappingSettingFilteredListSerializer, self).to_representation(data)


class MappingSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MappingSetting
        list_serializer_class = MappingSettingFilteredListSerializer
        fields = [
            'source_field',
            'destination_field',
            'import_to_fyle',
            'is_custom',
            'source_placeholder'
        ]


class ImportSettingFilterSerializer(serializers.ModelSerializer):
    """
    Import Settings Filtered serializer
    """
    class Meta:
        model = ImportSetting
        fields = [
            'import_categories',
            'import_vendors_as_merchants',
            'add_commitment_details',
            'import_code_fields'
        ]


class DependentFieldSettingSerializer(serializers.ModelSerializer):
    """
    Dependent Field serializer
    """
    cost_code_field_name = serializers.CharField(required=False)
    cost_category_field_name = serializers.CharField(required=False)

    class Meta:
        model = DependentFieldSetting
        fields = [
            'cost_code_field_name',
            'cost_code_placeholder',
            'cost_category_field_name',
            'cost_category_placeholder',
            'is_import_enabled',
        ]


class ImportSettingsSerializer(serializers.ModelSerializer):
    """
    Import Settings serializer
    """
    import_settings = ImportSettingFilterSerializer()
    mapping_settings = MappingSettingSerializer(many=True)
    dependent_field_settings = DependentFieldSettingSerializer(allow_null=True, required=False)
    workspace_id = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'import_settings',
            'mapping_settings',
            'dependent_field_settings',
            'workspace_id'
        ]
        read_only_fields = ['workspace_id']

    def get_workspace_id(self, instance):
        return instance.id

    def update(self, instance, validated):
        """
        Create Import Settings
        """

        mapping_settings = validated.pop('mapping_settings')
        import_settings = validated.pop('import_settings')
        dependent_field_settings = validated.pop('dependent_field_settings')

        import_code_fields = import_settings.get('import_code_fields', [])

        with transaction.atomic():
            ImportSetting.objects.update_or_create(
                workspace_id=instance.id,
                defaults={
                    'import_categories': import_settings.get('import_categories'),
                    'import_vendors_as_merchants': import_settings.get('import_vendors_as_merchants'),
                    'add_commitment_details': import_settings.get('add_commitment_details'),
                    'import_code_fields': import_code_fields
                }
            )

            trigger: ImportSettingsTrigger = ImportSettingsTrigger(
                mapping_settings=mapping_settings,
                workspace_id=instance.id
            )

            trigger.pre_save_mapping_settings()

            for setting in mapping_settings:
                MappingSetting.objects.update_or_create(
                    destination_field=setting['destination_field'],
                    workspace_id=instance.id,
                    defaults={
                        'source_field': setting['source_field'],
                        'import_to_fyle': setting['import_to_fyle'] if 'import_to_fyle' in setting else False,
                        'is_custom': setting['is_custom'] if 'is_custom' in setting else False,
                        'source_placeholder': setting['source_placeholder'] if 'source_placeholder' in setting else None
                    }
                )

            project_mapping = MappingSetting.objects.filter(workspace_id=instance.id, destination_field='JOB').first()
            if project_mapping and project_mapping.import_to_fyle and dependent_field_settings:
                DependentFieldSetting.objects.update_or_create(
                    workspace_id=instance.id,
                    defaults=dependent_field_settings
                )

            trigger.post_save_mapping_settings()

        # Update workspace onboarding state
        if instance.onboarding_state == 'IMPORT_SETTINGS':
            instance.onboarding_state = 'ADVANCED_SETTINGS'
            instance.save()

        return instance

    def validate(self, data):
        if not data.get('import_settings'):
            raise serializers.ValidationError('Import Settings are required')

        if data.get('mapping_settings') is None:
            raise serializers.ValidationError('Mapping settings are required')

        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        import_settings = ImportSetting.objects.filter(workspace_id=workspace_id).first()
        import_logs = ImportLog.objects.filter(workspace_id=workspace_id).values_list('attribute_type', flat=True)

        is_errored = False
        old_code_pref_list = set()

        if import_settings:
            old_code_pref_list = set(import_settings.import_code_fields)

        new_code_pref_list = set(data.get('import_settings', {}).get('import_code_fields', []))
        diff_code_pref_list = list(old_code_pref_list.symmetric_difference(new_code_pref_list))

        logger.info("Import Settings import_code_fields | Content: {{WORKSPACE_ID: {}, Old Import Code Fields: {}, New Import Code Fields: {}}}".format(workspace_id, old_code_pref_list if old_code_pref_list else {}, new_code_pref_list if new_code_pref_list else {}))
        """ If the JOB is in the code_fields then we also add Dep fields"""
        mapping_settings = data.get('mapping_settings', [])
        for setting in mapping_settings:
            if setting['destination_field'] == 'JOB' and 'JOB' in new_code_pref_list:
                if setting['source_field'] == 'PROJECT':
                    new_code_pref_list.update(['COST_CODE', 'COST_CATEGORY'])
                else:
                    old_code_pref_list.difference_update(['COST_CODE', 'COST_CATEGORY'])

            if setting['destination_field'] in diff_code_pref_list and setting['source_field'] in import_logs:
                is_errored = True
                break

        if 'ACCOUNT' in diff_code_pref_list and 'CATEGORY' in import_logs:
            is_errored = True

        if 'VENDOR' in diff_code_pref_list and 'MERCHANT' in import_logs:
            is_errored = True

        if not old_code_pref_list.issubset(new_code_pref_list):
            is_errored = True

        if is_errored:
            raise serializers.ValidationError('Cannot change the code fields once they are imported')

        data.get('import_settings')['import_code_fields'] = list(new_code_pref_list)

        return data


class AdvancedSettingSerializer(serializers.ModelSerializer):
    """
    Advanced Settings serializer
    """
    class Meta:
        model = AdvancedSetting
        fields = [
            'expense_memo_structure',
            'schedule_is_enabled',
            'interval_hours',
            'emails_selected',
            'emails_added',
            'auto_create_vendor',
            'sync_sage_300_to_fyle_payments',
            'is_real_time_export_enabled'
        ]
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

        AdvancedSettingsTriggers.run_post_advance_settings_triggers(workspace_id, advanced_setting)
        if workspace.onboarding_state == 'ADVANCED_SETTINGS':
            workspace.onboarding_state = 'COMPLETE'
            workspace.save()
            async_task('apps.workspaces.tasks.async_create_admin_subcriptions', workspace.id)
            AdvancedSettingsTriggers.post_to_integration_settings(workspace_id, True)

        return advanced_setting


class WorkspaceAdminSerializer(serializers.Serializer):
    """
    Workspace Admin Serializer
    """
    admin_emails = serializers.SerializerMethodField()

    def get_admin_emails(self, validated_data):
        """
        Get Workspace Admins
        """
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        workspace = Workspace.objects.get(id=workspace_id)
        admin_emails = []

        users = workspace.user.all()

        for user in users:
            admin = User.objects.get(user_id=user)
            employee = ExpenseAttribute.objects.filter(value=admin.email, workspace_id=workspace_id, attribute_type='EMPLOYEE').first()
            if employee:
                admin_emails.append({'name': employee.detail['full_name'], 'email': admin.email})

        return admin_emails
