"""
Fyle Signal
"""
import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from rest_framework.exceptions import ValidationError


from fyle_integrations_platform_connector import PlatformConnector

from apps.workspaces.models import FyleCredential
from apps.fyle.models import DependentFieldSetting, ExpenseFilter
from apps.sage300.dependent_fields import create_dependent_custom_field_in_fyle
from apps.fyle.tasks import re_run_skip_export_rule
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

    instance.project_field_id = platform.dependent_fields.get_project_field_id()

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
        fyle_attribute_type=instance.cost_category_field_name,
        platform=platform,
        source_placeholder=instance.cost_category_placeholder,
        parent_field_id=instance.cost_code_field_id,
    )
    instance.cost_category_field_id = cost_category['data']['id']


@receiver(post_save, sender=ExpenseFilter)
def run_post_save_expense_filters(sender, instance: ExpenseFilter, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    if instance.join_by is None:
        try:
            re_run_skip_export_rule(instance.workspace)
        except Exception as e:
            raise e
            logger.error(f'Error while processing expense filter for workspace: {instance.workspace.id} - {str(e)}')
            raise ValidationError('Failed to process expense filter')
