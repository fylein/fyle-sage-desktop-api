import logging
from datetime import datetime
from typing import List, Dict
from apps.mappings.imports.modules.base import Base
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
from apps.mappings.models import ImportLog
from apps.mappings.exceptions import handle_import_exceptions
from apps.workspaces.models import FyleCredential, ImportSetting
from fyle_integrations_platform_connector import PlatformConnector
from apps.mappings.helpers import prepend_code_to_name

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class Merchant(Base):
    """
    Class for Merchant module
    """
    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime, use_code_in_naming: bool = False):
        super().__init__(
            workspace_id=workspace_id,
            source_field='MERCHANT',
            destination_field=destination_field,
            platform_class_name='merchants',
            sync_after=sync_after,
            use_code_in_naming=use_code_in_naming
        )

    def trigger_import(self):
        """
        Trigger import for Merchant module
        """
        self.check_import_log_and_start_import()

    # remove the is_auto_sync_status_allowed parameter
    def construct_fyle_payload(
        self,
        paginated_destination_attributes: List[DestinationAttribute],
        existing_fyle_attributes_map: object,
        is_auto_sync_status_allowed: bool
    ):
        """
        Construct Fyle payload for Merchant module
        :param paginated_destination_attributes: List of paginated destination attributes
        :param existing_fyle_attributes_map: Existing Fyle attributes map
        :param is_auto_sync_status_allowed: Is auto sync status allowed
        :return: Fyle payload
        """
        payload = []

        for attribute in paginated_destination_attributes:
            # Create a new merchant if it does not exist in Fyle
            if attribute.value.lower() not in existing_fyle_attributes_map:
                payload.append(attribute.value)

        return payload

    # import_destination_attribute_to_fyle method is overridden
    @handle_import_exceptions
    def import_destination_attribute_to_fyle(self, import_log: ImportLog):
        """
        Import destiantion_attributes field to Fyle and Auto Create Mappings
        :param import_log: ImportLog object
        """
        fyle_credentials = FyleCredential.objects.get(workspace_id=self.workspace_id)
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        self.sync_expense_attributes(platform)

        self.sync_destination_attributes(self.destination_field)

        self.construct_payload_and_import_to_fyle(platform, import_log)

        self.sync_expense_attributes(platform)


def disable_merchants(workspace_id: int, merchants_to_disable: Dict, is_import_to_fyle_enabled: bool = False, *args, **kwargs):
    """
    merchants_to_disable object format:
    {
        'destination_id': {
            'value': 'old_merchant_name',
            'updated_value': 'new_merchant_name',
            'code': 'old_code',
            'updated_code': 'new_code' ---- if the code is updated else same as code
        }
    }
    """
    if not is_import_to_fyle_enabled or len(merchants_to_disable) == 0:
        logger.info("Skipping disabling merchants in Fyle | WORKSPACE_ID: %s", workspace_id)
        return

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    use_code_in_naming = ImportSetting.objects.filter(workspace_id = workspace_id, import_code_fields__contains=['VENDOR']).first()
    logger.info(f"Inside disable_merchants | WORKSPACE_ID: {workspace_id} | USE_CODE_IN_NAMING: {use_code_in_naming}")
    merchant_values = []
    for merchant_map in merchants_to_disable.values():
        if not use_code_in_naming and merchant_map['value'] == merchant_map['updated_value']:
            logger.info(f"Skipping2 disabling merchant {merchant_map['value']} in Fyle | WORKSPACE_ID: {workspace_id}")
            continue
        elif use_code_in_naming and (merchant_map['value'] == merchant_map['updated_value'] and merchant_map['code'] == merchant_map['updated_code']):
            logger.info(f"Skipping3 disabling merchant {merchant_map['value']} in Fyle | WORKSPACE_ID: {workspace_id}")
            continue

        merchant_name = prepend_code_to_name(prepend_code_in_name=use_code_in_naming, value=merchant_map['value'], code=merchant_map['code'])
        merchant_values.append(merchant_name)

    filters = {
        'workspace_id': workspace_id,
        'attribute_type': 'MERCHANT',
        'value__in': merchant_values,
        'active': True
    }
    logger.info("Filters: %s", filters)

    bulk_payload = ExpenseAttribute.objects.filter(**filters).values_list('value', flat=True)
    logger.info("Bulk Payload: %s", bulk_payload)
    if bulk_payload:
        logger.info(f"Disabling Merchants in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_payload)}")
        platform.merchants.post(bulk_payload, delete_merchants=True)
    else:
        logger.info(f"No Merchants to Disable in Fyle | WORKSPACE_ID: {workspace_id}")

    return bulk_payload
