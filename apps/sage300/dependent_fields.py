import logging
from datetime import datetime
from typing import Dict, List
from time import sleep
from django.contrib.postgres.aggregates import ArrayAgg

from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector

from apps.fyle.models import DependentFieldSetting
from apps.sage300.models import CostCategory
from apps.fyle.helpers import connect_to_platform
from apps.mappings.tasks import sync_sage300_attributes


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_custom_field_placeholder(source_placeholder: str, fyle_attribute: str, existing_attribute: Dict):
    new_placeholder = None
    placeholder = None

    if existing_attribute:
        placeholder = existing_attribute['placeholder'] if 'placeholder' in existing_attribute else None

    # Here is the explanation of what's happening in the if-else ladder below
    # source_field is the field that's save in mapping settings, this field user may or may not fill in the custom field form
    # placeholder is the field that's saved in the detail column of destination attributes
    # fyle_attribute is what we're constructing when both of these fields would not be available

    if not (source_placeholder or placeholder):
        # If source_placeholder and placeholder are both None, then we're creating adding a self constructed placeholder
        new_placeholder = 'Select {0}'.format(fyle_attribute)
    elif not source_placeholder and placeholder:
        # If source_placeholder is None but placeholder is not, then we're choosing same place holder as 1 in detail section
        new_placeholder = placeholder
    elif source_placeholder and not placeholder:
        # If source_placeholder is not None but placeholder is None, then we're choosing the placeholder as filled by user in form
        new_placeholder = source_placeholder
    else:
        # Else, we're choosing the placeholder as filled by user in form or None
        new_placeholder = source_placeholder

    return new_placeholder


def create_dependent_custom_field_in_fyle(workspace_id: int, fyle_attribute_type: str, platform: PlatformConnector, parent_field_id: str, source_placeholder: str = None):
    existing_attribute = ExpenseAttribute.objects.filter(
        attribute_type=fyle_attribute_type,
        workspace_id=workspace_id
    ).values_list('detail', flat=True).first()

    placeholder = construct_custom_field_placeholder(source_placeholder, fyle_attribute_type, existing_attribute)

    expense_custom_field_payload = {
        'field_name': fyle_attribute_type,
        'column_name': fyle_attribute_type,
        'type': 'DEPENDENT_SELECT',
        'is_custom': True,
        'is_enabled': True,
        'is_mandatory': False,
        'placeholder': placeholder,
        'options': [],
        'parent_field_id': parent_field_id,
        'code': None
    }

    return platform.expense_custom_fields.post(expense_custom_field_payload)


def post_dependent_cost_code(dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: Dict) -> List[str]:

    projects = CostCategory.objects.filter(**filters).values('job_name').annotate(cost_codes=ArrayAgg('cost_code_name', distinct=True))
    projects_from_categories = [project['job_name'] for project in projects]

    posted_cost_codes = []

    existing_projects_in_fyle = ExpenseAttribute.objects.filter(
        workspace_id=dependent_field_setting.workspace_id,
        attribute_type='PROJECT',
        value__in=projects_from_categories
    ).values_list('value', flat=True)

    for project in projects:
        payload = []
        cost_code_names = []

        for cost_code in project['cost_codes']:
            if project['job_name'] in existing_projects_in_fyle:
                payload.append({
                    'parent_expense_field_id': dependent_field_setting.project_field_id,
                    'parent_expense_field_value': project['job_name'],
                    'expense_field_id': dependent_field_setting.cost_code_field_id,
                    'expense_field_value': cost_code,
                    'is_enabled': True
                })
                cost_code_names.append(cost_code)

        if payload:
            sleep(0.2)
            platform.dependent_fields.bulk_post_dependent_expense_field_values(payload)
            posted_cost_codes.append(cost_code_names)

    return posted_cost_codes


def post_dependent_cost_type(dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: Dict):
    cost_categories = CostCategory.objects.filter(**filters).values('cost_code_name').annotate(cost_categories=ArrayAgg('name', distinct=True))

    for category in cost_categories:
        payload = [
            {
                'parent_expense_field_id': dependent_field_setting.cost_code_field_id,
                'parent_expense_field_value': category['cost_code_name'],
                'expense_field_id': dependent_field_setting.cost_category_field_id,
                'expense_field_value': cost_type,
                'is_enabled': True
            } for cost_type in category['cost_categories']
        ]

        if payload:
            sleep(0.2)
            platform.dependent_fields.bulk_post_dependent_expense_field_values(payload)


def post_dependent_expense_field_values(workspace_id: int, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector = None):
    if not platform:
        platform = connect_to_platform(workspace_id)

    filters = {
        'workspace_id': workspace_id
    }

    if dependent_field_setting.last_successful_import_at:
        filters['updated_at__gte'] = dependent_field_setting.last_successful_import_at

    posted_cost_types = post_dependent_cost_code(dependent_field_setting, platform, filters)
    if posted_cost_types:
        filters['cost_code_name__in'] = posted_cost_types
        post_dependent_cost_type(dependent_field_setting, platform, filters)

    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(last_successful_import_at=datetime.now())


def import_dependent_fields_to_fyle(workspace_id: str):
    dependent_field = DependentFieldSetting.objects.get(workspace_id=workspace_id)

    try:
        platform = connect_to_platform(workspace_id)
        sync_sage300_attributes('JOB', workspace_id)
        post_dependent_expense_field_values(workspace_id, dependent_field, platform)
    except Exception as exception:
        logger.error('Exception while importing dependent fields to fyle - %s', exception)
