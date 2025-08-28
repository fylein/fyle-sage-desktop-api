import logging
from datetime import datetime, timezone
from typing import Dict, List

from django.conf import settings
from django.db.models import Q
from apps.accounting_exports.models import AccountingExportSummary
from apps.sage300.actions import update_accounting_export_summary
from apps.workspaces.helpers import clear_workspace_errors_on_export_type_change
from fyle_accounting_mappings.models import ExpenseAttribute, MappingSetting

from apps.fyle.helpers import post_request
from apps.mappings.schedules import schedule_or_delete_fyle_import_tasks
from apps.workspaces.models import AdvancedSetting, ExportSetting, FyleCredential, ImportSetting, Workspace
from apps.workspaces.tasks import schedule_sync
from fyle_integrations_imports.models import ImportLog

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSettingsTrigger:
    """
    All the post save actions of Import Settings API
    """
    def __init__(self, mapping_settings: List[Dict], workspace_id):
        self.__mapping_settings = mapping_settings
        self.__workspace_id = workspace_id

    def __unset_auto_mapped_flag(self, current_mapping_settings: list[MappingSetting], new_mappings_settings: list[dict]) -> None:
        """
        Set the auto_mapped flag to false for the expense_attributes for the attributes
        whose mapping is changed.
        """
        changed_source_fields = []

        for new_setting in new_mappings_settings:
            destination_field = new_setting['destination_field']
            source_field = new_setting['source_field']
            current_setting = current_mapping_settings.filter(destination_field=destination_field).first()
            if current_setting and current_setting.source_field != source_field:
                changed_source_fields.append(current_setting.source_field)

        ExpenseAttribute.objects.filter(workspace_id=self.__workspace_id, attribute_type__in=changed_source_fields).update(auto_mapped=False)

    def __reset_import_log_timestamp(
            self,
            current_mapping_settings: List[MappingSetting],
            new_mappings_settings: List[Dict],
            workspace_id: int
    ) -> None:
        """
        Reset Import logs when mapping settings are deleted or the source_field is changed.
        """
        changed_source_fields = set()

        for new_setting in new_mappings_settings:
            destination_field = new_setting['destination_field']
            source_field = new_setting['source_field']
            current_setting = current_mapping_settings.filter(source_field=source_field).first()
            if current_setting and current_setting.destination_field != destination_field:
                changed_source_fields.add(source_field)

        current_source_fields = set(mapping_setting.source_field for mapping_setting in current_mapping_settings)
        new_source_fields = set(mapping_setting['source_field'] for mapping_setting in new_mappings_settings)
        deleted_source_fields = current_source_fields.difference(new_source_fields | {'CORPORATE_CARD', 'CATEGORY'})

        reset_source_fields = changed_source_fields.union(deleted_source_fields)

        ImportLog.objects.filter(workspace_id=workspace_id, attribute_type__in=reset_source_fields).update(last_successful_run_at=None, updated_at=datetime.now(timezone.utc))

    def pre_save_mapping_settings(self) -> None:
        """
        Pre save action for mapping settings
        """
        mapping_settings = self.__mapping_settings

        current_mapping_settings = MappingSetting.objects.filter(workspace_id=self.__workspace_id).all()
        self.__unset_auto_mapped_flag(current_mapping_settings, mapping_settings)
        self.__reset_import_log_timestamp(
            current_mapping_settings=current_mapping_settings,
            new_mappings_settings=mapping_settings,
            workspace_id=self.__workspace_id
        )

    def post_save_mapping_settings(self):
        """
        Post save actions for mapping settings
        Here we need to clear out the data from the mapping-settings table for consecutive runs.
        """
        # We first need to avoid deleting mapping-settings that are always necessary.
        destination_fields = [
            'ACCOUNT',
            'CCC_ACCOUNT',
            'CHARGE_CARD_NUMBER',
            'EMPLOYEE',
            'EXPENSE_TYPE',
            'TAX_DETAIL',
            'VENDOR'
        ]

        # Here we are filtering out the mapping_settings payload and adding the destination-fields that are present in the payload
        # So that we avoid deleting them.
        for setting in self.__mapping_settings:
            if setting['destination_field'] not in destination_fields:
                destination_fields.append(setting['destination_field'])

        # Now that we have all the system necessary mapping-settings and the mapping-settings in the payload
        # This query will take care of deleting all the redundant mapping-settings that are not required.
        MappingSetting.objects.filter(
            ~Q(destination_field__in=destination_fields),
            workspace_id=self.__workspace_id
        ).delete()

        import_settings = ImportSetting.objects.filter(workspace_id=self.__workspace_id).first()

        schedule_or_delete_fyle_import_tasks(import_settings)


class AdvancedSettingsTriggers:
    """
    Class containing all triggers for advanced_settings
    """
    @staticmethod
    def run_post_advance_settings_triggers(workspace_id, advance_settings: AdvancedSetting):
        """
        Run advance settings triggers
        """

        schedule_sync(
            workspace_id=workspace_id,
            schedule_enabled=advance_settings.schedule_is_enabled,
            hours=advance_settings.interval_hours,
            email_added=advance_settings.emails_added,
            emails_selected=advance_settings.emails_selected
        )

    @staticmethod
    def post_to_integration_settings(workspace_id: int, active: bool):
        """
        Post to integration settings
        """
        refresh_token = FyleCredential.objects.get(workspace_id=workspace_id).refresh_token
        url = '{}/integrations/'.format(settings.INTEGRATIONS_SETTINGS_API)
        payload = {
            'tpa_id': settings.FYLE_CLIENT_ID,
            'tpa_name': 'Fyle Sage 300 Integration',
            'type': 'ACCOUNTING',
            'is_active': active,
            'connected_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }

        try:
            post_request(url, payload, refresh_token)
            org_id = Workspace.objects.get(id=workspace_id).org_id
            logger.info(f'New integration record: Fyle Sage 300 Integration (ACCOUNTING) | {workspace_id} | {org_id}')

        except Exception as error:
            logger.error(error)


class ExportSettingsTrigger:
    """
    Class containing all triggers for export_settings
    """
    @staticmethod
    def post_save_workspace_general_settings(workspace_id: int, export_settings: ExportSetting, old_configurations: Dict):
        """
        Post save action for workspace general settings
        """

        export_settings: ExportSetting = ExportSetting.objects.filter(workspace_id=workspace_id).first()

        if old_configurations and export_settings:
            clear_workspace_errors_on_export_type_change(workspace_id, old_configurations, export_settings)

            last_export_detail = AccountingExportSummary.objects.filter(workspace_id=workspace_id).first()
            if last_export_detail.last_exported_at:
                update_accounting_export_summary(workspace_id)
