import logging
from datetime import datetime
from typing import List, Dict
from apps.mappings.imports.modules.base import Base
from apps.sage300.models import CostCategory
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from apps.sage300.dependent_fields import update_and_disable_cost_code
from apps.mappings.helpers import prepend_code_to_name
from apps.workspaces.models import FyleCredential, ImportSetting

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class Project(Base):
    """
    Class for Project module
    """

    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime, use_code_in_naming: bool = False):
        super().__init__(
            workspace_id=workspace_id,
            source_field="PROJECT",
            destination_field=destination_field,
            platform_class_name="projects",
            sync_after=sync_after,
            use_code_in_naming=use_code_in_naming
        )

    def trigger_import(self):
        """
        Trigger import for Project module
        """
        self.check_import_log_and_start_import()

    def construct_fyle_payload(
        self,
        paginated_destination_attributes: List[DestinationAttribute],
        existing_fyle_attributes_map: object,
        is_auto_sync_status_allowed: bool
    ):
        """
        Construct Fyle payload for Project module
        :param paginated_destination_attributes: List of paginated destination attributes
        :param existing_fyle_attributes_map: Existing Fyle attributes map
        :param is_auto_sync_status_allowed: Is auto sync status allowed
        :return: Fyle payload
        """
        payload = []

        job_ids_in_cost_category = CostCategory.objects.filter(
            workspace_id = self.workspace_id,
            job_id__in = [attribute.destination_id for attribute in paginated_destination_attributes]
        ).values_list('job_id', flat=True).distinct()

        for attribute in paginated_destination_attributes:
            if attribute.destination_id in job_ids_in_cost_category:
                project = {
                    'name': attribute.value,
                    'code': attribute.destination_id,
                    'description': 'Sage 300 Project - {0}, Id - {1}'.format(
                        attribute.value,
                        attribute.destination_id
                    ),
                    'is_enabled': True if attribute.active is None else attribute.active
                }

                # Create a new project if it does not exist in Fyle
                if attribute.value.lower() not in existing_fyle_attributes_map:
                    payload.append(project)
                # Disable the existing project in Fyle if auto-sync status is allowed and the destination_attributes is inactive
                elif is_auto_sync_status_allowed and not attribute.active:
                    project['id'] = existing_fyle_attributes_map[attribute.value.lower()]
                    payload.append(project)

        return payload


def disable_projects(workspace_id: int, projects_to_disable: Dict, is_import_to_fyle_enabled: bool = False, *args, **kwargs):
    """
    Disable projects in Fyle when the projects are updated in Sage 300.
    This is a callback function that is triggered from accounting_mappings.
    projects_to_disable object format:
    {
        'destination_id': {
            'value': 'old_project_name',
            'updated_value': 'new_project_name',
            'code': 'old_project_code',
            'updated_code': 'new_project_code'
        }
    }

    """
    if not is_import_to_fyle_enabled or len(projects_to_disable) == 0:
        logger.info("Skipping disabling projects in Fyle | WORKSPACE_ID: %s", workspace_id)
        return

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    platform.projects.sync()

    use_code_in_naming = ImportSetting.objects.filter(
        workspace_id = workspace_id,
        import_code_fields__contains=['JOB']
    ).first()

    project_values = []
    for projects_map in projects_to_disable.values():
        if not use_code_in_naming and projects_map['value'] == projects_map['updated_value']:
            continue
        elif use_code_in_naming and (projects_map['value'] == projects_map['updated_value'] and projects_map['code'] == projects_map['update_code']):
            continue

        project_name = prepend_code_to_name(prepend_code_in_name=use_code_in_naming, value=projects_map['value'], code=projects_map['code'])
        project_values.append(project_name)

    filters = {
        'workspace_id': workspace_id,
        'attribute_type': 'PROJECT',
        'value__in': project_values,
        'active': True
    }

    # Expense attribute value map is as follows: {old_project_name: destination_id}
    expense_attribute_value_map = {}
    for destination_id, v in projects_to_disable.items():
        project_name = prepend_code_to_name(prepend_code_in_name=use_code_in_naming, value=v['value'], code=v['code'])
        expense_attribute_value_map[project_name] = destination_id

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
            bulk_payload.append(payload)
        else:
            logger.error(f"Project with value {expense_attribute.value} not found | WORKSPACE_ID: {workspace_id}")

    if bulk_payload:
        logger.info(f"Disabling Projects in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_payload)}")
        platform.projects.post_bulk(bulk_payload)
        update_and_disable_cost_code(workspace_id, projects_to_disable, platform, use_code_in_naming)
        platform.projects.sync()
    else:
        logger.info(f"No Projects to Disable in Fyle | WORKSPACE_ID: {workspace_id}")

    return bulk_payload
