from datetime import datetime
from typing import List
from apps.mappings.imports.modules.base import Base
from fyle_accounting_mappings.models import DestinationAttribute, CategoryMapping


class Category(Base):
    """
    Class for Category module
    """

    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime):
        super().__init__(
            workspace_id=workspace_id,
            source_field="CATEGORY",
            destination_field=destination_field,
            platform_class_name="categories",
            sync_after=sync_after,
        )

    def trigger_import(self):
        """
        Trigger import for Category module
        """
        self.check_import_log_and_start_import()

    def construct_fyle_payload(
        self,
        paginated_destination_attributes: List[DestinationAttribute],
        existing_fyle_attributes_map: object
    ):
        """
        Construct Fyle payload for Category module
        :param paginated_destination_attributes: List of paginated destination attributes
        :param existing_fyle_attributes_map: Existing Fyle attributes map
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
            # Disable the existing category in Fyle if auto-sync status is
            # allowed and the destination_attributes is inactive
            elif not attribute.active:
                category["id"] = existing_fyle_attributes_map[attribute.value.lower()]
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
