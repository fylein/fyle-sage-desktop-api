from fyle_accounting_mappings.models import CategoryMapping, ExpenseAttribute, Mapping
from apps.accounting_exports.models import AccountingExport, Error

from sage_desktop_api.exceptions import BulkError


def get_filtered_mapping(
    source_field: str, destination_type: str, workspace_id: int, source_value: str, source_id: str) -> Mapping:
    filters = {
        'source_type': source_field,
        'destination_type': destination_type,
        'workspace_id': workspace_id
    }

    if source_id:
        filters['source__source_id'] = source_id
    else:
        filters['source__value'] = source_value

    return Mapping.objects.filter(**filters).first()


def validate_accounting_export(accounting_export: AccountingExport):
    bulk_errors = []
    row = 0

    expenses = accounting_export.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        category_attribute = ExpenseAttribute.objects.filter(
            value=category,
            workspace_id=accounting_export.workspace_id,
            attribute_type='CATEGORY'
        ).first()

        account = CategoryMapping.objects.filter(
            source_category_id=category_attribute.id,
            workspace_id=accounting_export.workspace_id
        ).first()

        if not account:
            bulk_errors.append({
                'row': row,
                'expense_group_id': accounting_export.id,
                'value': category,
                'type': 'Category Mapping',
                'message': 'Category Mapping not found'
            })

            if category_attribute:
                Error.objects.update_or_create(
                    workspace_id=accounting_export.workspace_id,
                    expense_attribute=category_attribute,
                    defaults={
                        'type': 'CATEGORY_MAPPING',
                        'error_title': category_attribute.value,
                        'error_detail': 'Category mapping is missing',
                        'is_resolved': False
                    }
                )

        row = row + 1

    if bulk_errors:
        raise BulkError('Mappings are missing', bulk_errors)
