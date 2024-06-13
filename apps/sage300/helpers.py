
from datetime import datetime, timezone
import logging

from typing import Dict
from django.utils.module_loading import import_string

from apps.workspaces.models import Workspace, Sage300Credential, FyleCredential
from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from apps.sage300.models import CostCategory
from apps.fyle.models import DependentFieldSetting
from apps.sage300.dependent_fields import post_dependent_cost_code
from apps.mappings.models import ImportLog

logger = logging.getLogger(__name__)
logger.level = logging.INFO


# Import your Workspace and Sage300Credential models here
# Also, make sure you have 'logger' defined and imported from a logging module
def check_interval_and_sync_dimension(workspace: Workspace, sage300_credential: Sage300Credential) -> bool:
    """
    Check the synchronization interval and trigger dimension synchronization if needed.

    :param workspace: Workspace Instance
    :param sage300_credential: Sage300Credential Instance

    :return: True if synchronization is triggered, False if not
    """

    if workspace.destination_synced_at:
        # Calculate the time interval since the last destination sync
        time_interval = datetime.now(timezone.utc) - workspace.destination_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        # If destination_synced_at is None or the time interval is greater than 0 days, trigger synchronization
        sync_dimensions(sage300_credential, workspace.id)
        return True

    return False


def sync_dimensions(sage300_credential: Sage300Credential, workspace_id: int) -> None:
    """
    Synchronize various dimensions with Sage 300 using the provided credentials.

    :param sage300_credential: Sage300Credential Instance
    :param workspace_id: ID of the workspace

    This function syncs dimensions like accounts, vendors, commitments, jobs, categories, and cost codes.
    """
    # Initialize the Sage 300 connection using the provided credentials and workspace ID
    sage300_connection = import_string('apps.sage300.utils.SageDesktopConnector')(sage300_credential, workspace_id)

    # List of dimensions to sync
    dimensions = ['accounts', 'vendors', 'jobs', 'commitments', 'commitment_items', 'standard_categories', 'standard_cost_codes',  'cost_codes', 'cost_categories']

    for dimension in dimensions:
        try:
            # Dynamically call the sync method based on the dimension
            sync = getattr(sage300_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            # Log any exceptions that occur during synchronization
            logger.info(exception)


def disable_projects(workspace_id: int, projects_to_disable: Dict):
    """
    Disable projects in Fyle when the projects are updated in Sage 300.
    This is a callback function that is triggered from accounting_mappings.
    projects_to_disable object format:
    {
        'destination_id': {
            'value': 'old_project_name',
            'updated_value': 'new_project_name'
        }
    }

    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    platform.projects.sync()

    filters = {
        'workspace_id': workspace_id,
        'attribute_type': 'PROJECT',
        'value__in': [projects_map['value'] for projects_map in projects_to_disable.values()],
        'active': True
    }

    # Expense attribute value map is as follows: {old_project_name: destination_id}
    expense_attribute_value_map = {v['value']: k for k, v in projects_to_disable.items()}

    expense_attributes = ExpenseAttribute.objects.filter(**filters)

    bulk_payload = []
    for expense_attribute in expense_attributes:
        code = expense_attribute_value_map.get(expense_attribute.value, None)
        if code:
            payload = {
                'name': expense_attribute.value,
                'code': code,
                'description': 'Sage 300 Project - {0}, Id - {1}'.format(
                    expense_attribute.value,
                    code
                ),
                'is_enabled': False,
                'id': expense_attribute.source_id
            }
        else:
            logger.error(f"Project with value {expense_attribute.value} not found | WORKSPACE_ID: {workspace_id}")

        bulk_payload.append(payload)

    if bulk_payload:
        logger.info(f"Disabling Projects in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_payload)}")
        platform.projects.post_bulk(bulk_payload)
    else:
        logger.info(f"No Projects to Disable in Fyle | WORKSPACE_ID: {workspace_id}")

    update_and_disable_cost_code(workspace_id, projects_to_disable, platform)
    platform.projects.sync()


def update_and_disable_cost_code(workspace_id: int, cost_codes_to_disable: Dict, platform: PlatformConnector):
    """
    Update the job_name in CostCategory and disable the old cost code in Fyle
    """
    dependent_field_setting = DependentFieldSetting.objects.filter(is_import_enabled=True, workspace_id=workspace_id).first()

    if dependent_field_setting:
        filters = {
            'job_id__in':list(cost_codes_to_disable.keys()),
            'workspace_id': workspace_id
        }
        cost_code_import_log = ImportLog.create('COST_CODE', workspace_id)
        logger.info("Filters for Cost Code Import Log: %s", filters)
        # This call will disable the cost codes in Fyle that has old project name
        posted_cost_codes = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters, is_enabled=False)

        logger.info(f"Disabled Cost Codes in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(posted_cost_codes)}")

        # here we are updating the CostCategory with the new project name
        bulk_update_payload = []
        for destination_id, value in cost_codes_to_disable.items():
            cost_categories = CostCategory.objects.filter(
                workspace_id=workspace_id,
                job_id=destination_id
            ).exclude(job_name=value['updated_value'])

            for cost_category in cost_categories:
                cost_category.job_name = value['updated_value']
                cost_category.updated_at = datetime.now(timezone.utc)
                cost_category.is_imported = False
                bulk_update_payload.append(cost_category)

        if bulk_update_payload:
            logger.info(f"Updating Cost Categories | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_update_payload)}")
            CostCategory.objects.bulk_update(bulk_update_payload, ['job_name', 'updated_at', 'is_imported'], batch_size=50)
