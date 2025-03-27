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
    job_code = models.CharField(max_length=255, null=True, help_text='Job - Code')
    cost_code_code = models.CharField(max_length=255, null=True, help_text='Cost_Code - Code')
    cost_category_code = models.CharField(max_length=255, null=True, help_text='Cost_Category - Code')

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
            'status',
            'job_code',
            'cost_code_code',
            'cost_category_code'
        )
        existing_cost_type_record_numbers = []
        primary_key_map = {}

        for existing_category in existing_categories:
            existing_cost_type_record_numbers.append(existing_category['cost_category_id'])
            primary_key_map[existing_category['cost_category_id']] = {
                'id': existing_category['id'],
                'name': existing_category['name'],
                'status': existing_category['status'],
                'job_code': existing_category['job_code'],
                'cost_code_code': existing_category['cost_code_code'],
                'cost_category_code': existing_category['cost_category_code'],
            }

        cost_category_to_be_created = []
        cost_category_to_be_updated = []
        jobs_to_be_updated = set()

        # Retrieve job names and cost code names in a single query
        cost_code_ids = [category.cost_code_id for category in list_of_categories]
        job_ids = [category.job_id for category in list_of_categories]

        jobs = DestinationAttribute.objects.filter(destination_id__in=job_ids, workspace_id=workspace_id)
        cost_codes = DestinationAttribute.objects.filter(destination_id__in=cost_code_ids, workspace_id=workspace_id)

        job_mapping = {}
        cost_code_mapping = {}

        for job in jobs:
            job_mapping[job.destination_id] = {
                'job_name': job.value,
                'code': job.code
            }

        for cost_code in cost_codes:
            cost_code_mapping[cost_code.destination_id] = {
                'cost_code_name': cost_code.value,
                'code': cost_code.code
            }

        for category in list_of_categories:
            job_name = job_mapping.get(category.job_id, {}).get('job_name')
            cost_code_name = cost_code_mapping.get(category.cost_code_id, {}).get('cost_code_name')
            cost_category_code = " ".join(category.code.split()) if category.code is not None else None
            if job_name and cost_code_name and category.is_active:
                jobs_to_be_updated.add(category.job_id)
                category_object = CostCategory(
                    job_id=category.job_id,
                    job_name=job_name,
                    cost_code_id=category.cost_code_id,
                    cost_code_name=" ".join(cost_code_name.split()),
                    name=" ".join(category.name.split()),
                    status=category.is_active,
                    cost_category_id=category.id,
                    workspace_id=workspace_id,
                    job_code=job_mapping.get(category.job_id)['code'],
                    cost_code_code=cost_code_mapping.get(category.cost_code_id)['code'],
                    cost_category_code=cost_category_code,
                    updated_at=datetime.now(timezone.utc)
                )

                if category.id not in existing_cost_type_record_numbers:
                    cost_category_to_be_created.append(category_object)

                elif category.id in primary_key_map.keys() and (
                    category.name != primary_key_map[category.id]['name'] or category.is_active != primary_key_map[category.id]['status']
                    or job_mapping.get(category.job_id)['code'] != primary_key_map[category.id]['job_code']
                    or cost_code_mapping.get(category.cost_code_id)['code'] != primary_key_map[category.id]['cost_code_code']
                    or cost_category_code != primary_key_map[category.id]['cost_category_code']
                ):
                    category_object.id = primary_key_map[category.id]['id']
                    cost_category_to_be_updated.append(category_object)

        if cost_category_to_be_created:
            CostCategory.objects.bulk_create(cost_category_to_be_created, batch_size=2000)

        if cost_category_to_be_updated:
            CostCategory.objects.bulk_update(
                cost_category_to_be_updated, fields=[
                    'job_id', 'job_name', 'cost_code_id', 'cost_code_name',
                    'name', 'status', 'cost_category_id',
                    'job_code', 'cost_code_code', 'cost_category_code', 'updated_at'
                ],
                batch_size=2000
            )

        if jobs_to_be_updated:
            updated_time = datetime.now(timezone.utc)
            DestinationAttribute.objects.filter(destination_id__in=list(jobs_to_be_updated), workspace_id=workspace_id).update(updated_at=updated_time)
