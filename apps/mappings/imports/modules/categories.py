import logging
from datetime import datetime
from typing import List, Dict
from apps.workspaces.models import ImportSetting, FyleCredential
from apps.mappings.imports.modules.base import Base
from apps.mappings.helpers import format_attribute_name
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, CategoryMapping

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class Category(Base):
    """
    Class for Category module
    """

    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime, use_code_in_naming: bool = False):
        super().__init__(
            workspace_id=workspace_id,
            source_field="CATEGORY",
            destination_field=destination_field,
            platform_class_name="categories",
            sync_after=sync_after,
            use_code_in_naming=use_code_in_naming
        )

    def trigger_import(self):
        """
        Trigger import for Category module
        """
        self.check_import_log_and_start_import()

    def construct_fyle_payload(
        self,
        paginated_destination_attributes: List[DestinationAttribute],
        existing_fyle_attributes_map: object,
        is_auto_sync_status_allowed: bool
    ):
        """
        Construct Fyle payload for Category module
        :param paginated_destination_attributes: List of paginated destination attributes
        :param existing_fyle_attributes_map: Existing Fyle attributes map
        :param is_auto_sync_status_allowed: Is auto sync status allowed
        :return: Fyle payload
        """
        payload = []

        for attribute in paginated_destination_attributes:
            category = {
                "name": attribute.value,
                "code": attribute.destination_id,
                "is_enabled": attribute.active,
            }

            # Create a new category if it does not exist in Fyle
            if attribute.value.lower() not in existing_fyle_attributes_map:
                payload.append(category)
            # Disable the existing category in Fyle if auto-sync status is allowed and the destination_attributes is inactive
            elif is_auto_sync_status_allowed and not attribute.active:
                category['id'] = existing_fyle_attributes_map[attribute.value.lower()]
                payload.append(category)

        return payload

    def create_mappings(self):
        """
        Create mappings for Category module
        """
        filters = {
            "workspace_id": self.workspace_id,
            "attribute_type": self.destination_field,
            "destination_account__isnull": True
        }

        # get all the destination attributes that have category mappings as null
        destination_attributes: List[
            DestinationAttribute
        ] = DestinationAttribute.objects.filter(**filters)

        destination_attributes_without_duplicates = []
        destination_attributes_without_duplicates = self.remove_duplicate_attributes(
            destination_attributes
        )

        CategoryMapping.bulk_create_mappings(
            destination_attributes_without_duplicates,
            self.destination_field,
            self.workspace_id,
        )


def disable_categories(workspace_id: int, categories_to_disable: Dict):
    """
    categories_to_disable object format:
    {
        'destination_id': {
            'value': 'old_category_name',
            'updated_value': 'new_category_name',
            'code': 'old_code',
            'update_code': 'new_code' ---- if the code is updated else same as code
        }
    }
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    use_code_in_naming = ImportSetting.objects.filter(workspace_id=workspace_id, import_code_fields__contains=['ACCOUNT']).first()
    category_account_mapping = CategoryMapping.objects.filter(
        workspace_id=workspace_id,
        destination_account__destination_id__in=categories_to_disable.keys()
    )

    logger.info(f"Deleting Category-Account Mappings | WORKSPACE_ID: {workspace_id} | COUNT: {category_account_mapping.count()}")
    category_account_mapping.delete()

    category_values = []
    for category_map in categories_to_disable.values():
        category_name = format_attribute_name(use_code_in_naming=use_code_in_naming, attribute_name=category_map['value'], attribute_code=category_map['code'])
        category_values.append(category_name)

    filters = {
        'workspace_id': workspace_id,
        'attribute_type': 'CATEGORY',
        'value__in': category_values,
        'active': True
    }

    # Expense attribute value map is as follows: {old_category_name: destination_id}
    expense_attribute_value_map = {}
    for k, v in categories_to_disable.items():
        category_name = format_attribute_name(use_code_in_naming=use_code_in_naming, attribute_name=v['value'], attribute_code=v['code'])
        expense_attribute_value_map[category_name] = k

    expense_attributes = ExpenseAttribute.objects.filter(**filters)

    bulk_payload = []
    for expense_attribute in expense_attributes:
        code = expense_attribute_value_map.get(expense_attribute.value, None)
        if code:
            payload = {
                'name': expense_attribute.value,
                'code': code,
                'is_enabled': False,
                'id': expense_attribute.source_id
            }
            bulk_payload.append(payload)
        else:
            logger.error(f"Category not found in categories_to_disable: {expense_attribute.value}")

    if bulk_payload:
        logger.info(f"Disabling Category in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_payload)}")
        platform.categories.post_bulk(bulk_payload)
    else:
        logger.info(f"No Categories to Disable in Fyle | WORKSPACE_ID: {workspace_id}")

    return bulk_payload
