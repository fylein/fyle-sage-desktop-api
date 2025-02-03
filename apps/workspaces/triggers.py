from datetime import datetime
import json
import logging
from typing import Dict, List
from django.conf import settings
from django.db.models import Q

from apps.fyle.helpers import post_request
from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks
from apps.workspaces.models import FyleCredential, ImportSetting, Workspace
from fyle_accounting_mappings.models import MappingSetting

from apps.workspaces.models import AdvancedSetting
from apps.workspaces.tasks import schedule_sync

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSettingsTrigger:
    """
    All the post save actions of Import Settings API
    """
    def __init__(self, mapping_settings: List[Dict], workspace_id):
        self.__mapping_settings = mapping_settings
        self.__workspace_id = workspace_id

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
            logger.info(f'New integration record: Fyle Sage 300 Integration (ACCOUNTING) | {workspace_id = } | {org_id = }')

        except Exception as error:
            logger.error(error)
