from datetime import datetime
from typing import List
from apps.mappings.imports.modules.base import Base
from fyle_accounting_mappings.models import DestinationAttribute


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
