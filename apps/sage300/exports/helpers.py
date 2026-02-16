import itertools
from datetime import datetime, timedelta, timezone

from fyle_accounting_mappings.models import CategoryMapping, EmployeeMapping, ExpenseAttribute, Mapping

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
                error, created = Error.get_or_create_error_with_accounting_export(accounting_export, category_attribute)
                error.increase_repetition_count_by_one(created)

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
            error, created = Error.get_or_create_error_with_accounting_export(accounting_export, employee_attribute)
            error.increase_repetition_count_by_one(created)

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
    Error.objects.filter(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, is_resolved=False).update(is_resolved=True, updated_at=datetime.now(timezone.utc))


def validate_failing_export(is_auto_export: bool, interval_hours: int, error: Error, accounting_export: AccountingExport = None) -> tuple:
    """
    Validate failing export
    :param is_auto_export: Is auto export
    :param interval_hours: Interval hours
    :param error: Error
    :param accounting_export: AccountingExport object
    :return: Tuple of (should_skip, is_mapping_error)
    """
    should_skip_repetition = (
        is_auto_export
        and interval_hours
        and error
        and error.repetition_count > 100
        and datetime.now().replace(tzinfo=timezone.utc) - error.updated_at <= timedelta(hours=24)
    )

    if should_skip_repetition:
        return True, False

    if accounting_export:
        mapping_error = Error.objects.filter(
            workspace_id=accounting_export.workspace_id,
            mapping_error_accounting_export_ids__contains=[accounting_export.id],
            is_resolved=False
        ).first()
        if mapping_error:
            return True, True

    return False, False
