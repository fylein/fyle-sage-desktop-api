import itertools
from datetime import datetime

from fyle_accounting_mappings.models import CategoryMapping, ExpenseAttribute, Mapping, EmployeeMapping
from apps.accounting_exports.models import AccountingExport, Error

from sage_desktop_api.exceptions import BulkError


def get_employee_expense_attribute(value: str, workspace_id: int) -> ExpenseAttribute:
    """
    Get employee expense attribute
    :param value: value
    :param workspace_id: workspace id
    """
    return ExpenseAttribute.objects.filter(
        attribute_type='EMPLOYEE',
        value=value,
        workspace_id=workspace_id
    ).first()


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


def __validate_category_mapping(accounting_export: AccountingExport):

    row = 0
    bulk_errors = []
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
                'accounting_export_id': accounting_export.id,
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

    return bulk_errors


def __validate_employee_mapping(accounting_export: AccountingExport):

    bulk_errors = []
    row = 0

    employee_email = accounting_export.description.get('employee_email')

    employee_attribute = get_employee_expense_attribute(employee_email, accounting_export.workspace_id)

    mapping = EmployeeMapping.objects.filter(
        source_employee=employee_attribute,
        workspace_id=accounting_export.workspace_id
    ).first()

    if not mapping:
        bulk_errors.append({
            'row': row,
            'accounting_export_id': accounting_export.id,
            'value': employee_email,
            'type': 'Employee Mapping',
            'message': 'Employee Mapping not found'
        })

        if employee_attribute:
            Error.objects.update_or_create(
                workspace_id=accounting_export.workspace_id,
                expense_attribute=employee_attribute,
                defaults={
                    'type': 'EMPLOYEE_MAPPING',
                    'error_title': employee_attribute.value,
                    'error_detail': 'Employee mapping is missing',
                    'is_resolved': False
                }
            )

        row = row + 1

    return bulk_errors


def validate_accounting_export(accounting_export: AccountingExport):
    category_mapping_errors = __validate_category_mapping(accounting_export)
    employee_mapping_errors = []

    if accounting_export.fund_source == 'PERSONAL':
        employee_mapping_errors = __validate_employee_mapping(accounting_export)

    bulk_errors = list(
        itertools.chain(
            category_mapping_errors, employee_mapping_errors
        )
    )

    if bulk_errors:
        raise BulkError('Mappings are missing', bulk_errors)


def resolve_errors_for_exported_accounting_export(accounting_export: AccountingExport):
    """
    Resolve errors for exported accounting export
    :param accounting_export: Accounting Export
    """
    Error.objects.filter(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, is_resolved=False).update(is_resolved=True)


def get_valid_date_format(invoice_date: str):
    """
    Get valid date format
    :param invoice_date: Invoice date
    :return: Formatted date string in '%Y-%m-%d' format if input matches the expected format, else return the original string
    """
    try:
        return datetime.strptime(invoice_date, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return datetime.strptime(invoice_date, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
