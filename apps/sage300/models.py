import logging
from datetime import datetime, timezone
from typing import List, Dict
from django.db import models

from fyle_accounting_mappings.models import (
    DestinationAttribute
)

from apps.workspaces.models import BaseForeignWorkspaceModel
from sage_desktop_api.models.fields import (
    StringNotNullField,
    BooleanFalseField
)
from sage_desktop_sdk.core.schema.read_only import Category

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class CostCategory(BaseForeignWorkspaceModel):
    """
    Cost Categories Table Model Class
    """

    id = models.AutoField(primary_key=True)
    job_id = StringNotNullField(help_text='Sage300 Job Id')
    job_name = StringNotNullField(help_text='Sage300 Job Name')
    cost_code_id = StringNotNullField(help_text='Sage300 Cost Code Id')
    cost_code_name = StringNotNullField(help_text='Sage300 Cost Code Name')
    name = StringNotNullField(help_text='Sage300 Cost Type Name')
    cost_category_id = StringNotNullField(help_text='Sage300 Category Id')
    status = BooleanFalseField(help_text='Sage300 Cost Type Status')
    is_imported = models.BooleanField(default=False, help_text='Is Imported')

    class Meta:
        db_table = 'cost_category'

    @staticmethod
    def bulk_create_or_update(categories: List[Dict], workspace_id: int):
        """
        Bulk create or update cost types
        """
        list_of_categories = []
        for data in categories:
            list_of_categories.append(Category.from_dict(data))

        record_number_list = [category.id for category in list_of_categories]

        filters = {
            'cost_category_id__in': record_number_list,
            'workspace_id': workspace_id
        }

        existing_categories = CostCategory.objects.filter(**filters).values(
            'id',
            'cost_category_id',
            'name',
            'status'
        )

        existing_cost_type_record_numbers = []
        primary_key_map = {}

        for existing_category in existing_categories:
            existing_cost_type_record_numbers.append(existing_category['cost_category_id'])
            primary_key_map[existing_category['cost_category_id']] = {
                'id': existing_category['id'],
                'name': existing_category['name'],
                'status': existing_category['status'],
            }

        cost_category_to_be_created = []
        cost_category_to_be_updated = []
        jobs_to_be_updated = set()

        # Retrieve job names and cost code names in a single query
        cost_code_ids = [category.cost_code_id for category in list_of_categories]
        job_ids = [category.job_id for category in list_of_categories]

        job_name_mapping = {attr.destination_id: attr.value for attr in DestinationAttribute.objects.filter(destination_id__in=job_ids, workspace_id=workspace_id)}
        cost_code_name_mapping = {attr.destination_id: attr.value for attr in DestinationAttribute.objects.filter(destination_id__in=cost_code_ids, workspace_id=workspace_id)}

        for category in list_of_categories:
            job_name = job_name_mapping.get(category.job_id)
            cost_code_name = cost_code_name_mapping.get(category.cost_code_id)
            if job_name and cost_code_name:
                jobs_to_be_updated.add(category.job_id)
                category_object = CostCategory(
                    job_id=category.job_id,
                    job_name=job_name,
                    cost_code_id=category.cost_code_id,
                    cost_code_name=" ".join(cost_code_name.split()),
                    name=" ".join(category.name.split()),
                    status=category.is_active,
                    cost_category_id=category.id,
                    workspace_id=workspace_id
                )

                if category.id not in existing_cost_type_record_numbers:
                    cost_category_to_be_created.append(category_object)

                elif category.id in primary_key_map.keys() and (
                    category.name != primary_key_map[category.id]['name'] or category.is_active != primary_key_map[category.id]['status']
                ):
                    category_object.id = primary_key_map[category.id]['cost_category_id']
                    cost_category_to_be_updated.append(category_object)

            else:
                logger.error(f"Job name with job_id {category.job_id} or cost code name with cost_code_id {category.cost_code_id} not found in workspace {workspace_id}")

        if cost_category_to_be_created:
            CostCategory.objects.bulk_create(cost_category_to_be_created, batch_size=2000)

        if cost_category_to_be_updated:
            CostCategory.objects.bulk_update(
                cost_category_to_be_updated, fields=[
                    'job_id', 'job_name', 'cost_code_id', 'cost_code_name',
                    'name', 'status', 'cost_category_id'
                ],
                batch_size=2000
            )

        if jobs_to_be_updated:
            updated_time = datetime.now(timezone.utc)
            DestinationAttribute.objects.filter(destination_id__in=list(jobs_to_be_updated), workspace_id=workspace_id).update(updated_at=updated_time)
