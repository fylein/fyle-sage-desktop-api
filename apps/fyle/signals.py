"""
Fyle Signal
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential
from apps.fyle.models import DependentFieldSetting
from apps.sage300.dependent_fields import create_dependent_custom_field_in_fyle

logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=DependentFieldSetting)
def run_pre_save_dependent_field_settings_triggers(sender, instance: DependentFieldSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    # Patch alert - Skip creating dependent fields if they're already created
    if instance.cost_code_field_id:
        return

    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=instance.workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    instance.project_field_id = platform.expense_fields.get_project_field_id()

    cost_code = create_dependent_custom_field_in_fyle(
        workspace_id=instance.workspace_id,
        fyle_attribute_type=instance.cost_code_field_name,
        platform=platform,
        source_placeholder=instance.cost_code_placeholder,
        parent_field_id=instance.project_field_id,
    )

    instance.cost_code_field_id = cost_code['data']['id']

    cost_category = create_dependent_custom_field_in_fyle(
        workspace_id=instance.workspace_id,
        fyle_attribute_type=instance.category_field_name,
        platform=platform,
        source_placeholder=instance.category_placeholder,
        parent_field_id=instance.cost_code_field_id,
    )
    instance.category_field_id = cost_category['data']['id']


@receiver(post_save, sender=DependentFieldSetting)
def run_post_save_dependent_field_settings_triggers(sender, instance: DependentFieldSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    pass
