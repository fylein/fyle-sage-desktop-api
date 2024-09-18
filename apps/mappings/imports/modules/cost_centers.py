import logging
from datetime import datetime
from typing import List, Dict
from apps.mappings.imports.modules.base import Base
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, MappingSetting
from apps.workspaces.models import FyleCredential, ImportSetting
from fyle_integrations_platform_connector import PlatformConnector
from apps.mappings.helpers import prepend_code_to_name

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class CostCenter(Base):
    """
    Class for Cost Center module
    """

    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime, use_code_in_naming: bool = False):
        super().__init__(
            workspace_id=workspace_id,
            source_field="COST_CENTER",
            destination_field=destination_field,
            platform_class_name="cost_centers",
            sync_after=sync_after,
            use_code_in_naming=use_code_in_naming
        )

    def trigger_import(self):
        """
        Trigger import for Cost Center module
        """
        self.check_import_log_and_start_import()

    def construct_fyle_payload(
        self,
        paginated_destination_attributes: List[DestinationAttribute],
        existing_fyle_attributes_map: object,
        is_auto_sync_status_allowed: bool
    ):
        """
        Construct Fyle payload for CostCenter module
        :param paginated_destination_attributes: List of paginated destination attributes
        :param existing_fyle_attributes_map: Existing Fyle attributes map
        :param is_auto_sync_status_allowed: Is auto sync status allowed
        :return: Fyle payload
        """
        payload = []

        for attribute in paginated_destination_attributes:
            cost_center = {
                'name': attribute.value,
                'code': attribute.destination_id,
                'is_enabled': True if attribute.active is None else attribute.active,
                'description': 'Cost Center - {0}, Id - {1}'.format(
                    attribute.value,
                    attribute.destination_id
                )
            }

            # Create a new cost-center if it does not exist in Fyle
            if attribute.value.lower() not in existing_fyle_attributes_map:
                payload.append(cost_center)

        return payload


def disable_cost_centers(workspace_id: int, cost_centers_to_disable: Dict, is_import_to_fyle_enabled: bool = False, *args, **kwargs):
    """
    cost_centers_to_disable object format:
    {
        'destination_id': {
            'value': 'old_cost_center_name',
            'updated_value': 'new_cost_center_name',
            'code': 'old_code',
            'updated_code': 'new_code' ---- if the code is updated else same as code
        }
    }
    """
    if not is_import_to_fyle_enabled or len(cost_centers_to_disable) == 0:
        logger.info("Skipping disabling cost centers in Fyle | WORKSPACE_ID: %s", workspace_id)
        return

    destination_type = MappingSetting.objects.get(workspace_id=workspace_id, source_field='COST_CENTER').destination_field
    use_code_in_naming = ImportSetting.objects.filter(workspace_id=workspace_id, import_code_fields__contains=[destination_type]).first()

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    cost_center_values = []
    for cost_center_map in cost_centers_to_disable.values():
        if not use_code_in_naming and cost_center_map['value'] == cost_center_map['updated_value']:
            continue
        elif use_code_in_naming and (cost_center_map['value'] == cost_center_map['updated_value'] and cost_center_map['code'] == cost_center_map['updated_code']):
            continue

        cost_center_name = prepend_code_to_name(prepend_code_in_name=use_code_in_naming, value=cost_center_map['value'], code=cost_center_map['code'])
        cost_center_values.append(cost_center_name)

    filters = {
        'workspace_id': workspace_id,
        'attribute_type': 'COST_CENTER',
        'value__in': cost_center_values,
        'active': True
    }

    expense_attribute_value_map = {}
    for destination_id, v in cost_centers_to_disable.items():
        cost_center_name = prepend_code_to_name(prepend_code_in_name=use_code_in_naming, value=v['value'], code=v['code'])
        expense_attribute_value_map[cost_center_name] = destination_id

    expense_attributes = ExpenseAttribute.objects.filter(**filters)

    bulk_payload = []
    for expense_attribute in expense_attributes:
        code = expense_attribute_value_map.get(expense_attribute.value, None)
        if code:
            payload = {
                'name': expense_attribute.value,
                'code': code,
                'is_enabled': False,
                'id': expense_attribute.source_id,
                'description': 'Cost Center - {0}, Id - {1}'.format(
                    expense_attribute.value,
                    code
                )
            }
            bulk_payload.append(payload)
        else:
            logger.error(f"Cost Center with value {expense_attribute.value} not found | WORKSPACE_ID: {workspace_id}")

    if bulk_payload:
        logger.info(f"Disabling Cost Center in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_payload)}")
        platform.cost_centers.post_bulk(bulk_payload)
    else:
        logger.info(f"No Cost Center to Disable in Fyle | WORKSPACE_ID: {workspace_id}")

    return bulk_payload
