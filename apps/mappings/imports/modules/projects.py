from datetime import datetime
from typing import List
from apps.mappings.imports.modules.base import Base
from apps.sage300.models import CostCategory
from fyle_accounting_mappings.models import DestinationAttribute


class Project(Base):
    """
    Class for Project module
    """

    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime):
        super().__init__(
            workspace_id=workspace_id,
            source_field="PROJECT",
            destination_field=destination_field,
            platform_class_name="projects",
            sync_after=sync_after,
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

    def construct_attributes_filter(self, attribute_type: str, paginated_destination_attribute_values: List[str] = []):
        """
        Construct the attributes filter
        :param attribute_type: attribute type
        :param paginated_destination_attribute_values: paginated destination attribute values
        :return: dict
        """
        filters = {
            'attribute_type': attribute_type,
            'workspace_id': self.workspace_id
        }

        if paginated_destination_attribute_values:
            filters['value__in'] = paginated_destination_attribute_values

        else:
            job_ids = CostCategory.objects.filter(
                workspace_id = self.workspace_id,
                is_imported = False
            ).values_list('job_id', flat=True).distinct()

            filters['destination_id__in'] = job_ids

        return filters
