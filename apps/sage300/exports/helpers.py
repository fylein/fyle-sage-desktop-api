import itertools
import logging
from datetime import datetime, timedelta, timezone

from fyle.platform.exceptions import InternalServerError, InvalidTokenError
from fyle_accounting_mappings.models import CategoryMapping, EmployeeMapping, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.models import FyleCredential
from sage_desktop_api.exceptions import BulkError

logger = logging.getLogger(__name__)
logger.level = logging.INFO


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


def sync_inactive_employee(accounting_export: AccountingExport) -> ExpenseAttribute:
    try:
        fyle_credentials = FyleCredential.objects.get(workspace_id=accounting_export.workspace_id)
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        fyle_employee = platform.employees.get_employee_by_email(accounting_export.description.get('employee_email'))
        if len(fyle_employee):
            fyle_employee = fyle_employee[0]
            attribute = {
                'attribute_type': 'EMPLOYEE',
                'display_name': 'Employee',
                'value': fyle_employee['user']['email'],
                'source_id': fyle_employee['id'],
                'active': True if fyle_employee['is_enabled'] and fyle_employee['has_accepted_invite'] else False,
                'detail': {
                    'user_id': fyle_employee['user_id'],
                    'employee_code': fyle_employee['code'],
                    'full_name': fyle_employee['user']['full_name'],
                    'location': fyle_employee['location'],
                    'department': fyle_employee['department']['name'] if fyle_employee['department'] else None,
                    'department_id': fyle_employee['department_id'],
                    'department_code': fyle_employee['department']['code'] if fyle_employee['department'] else None
                }
            }
            ExpenseAttribute.bulk_create_or_update_expense_attributes([attribute], 'EMPLOYEE', accounting_export.workspace_id, True)
            return get_employee_expense_attribute(accounting_export.description.get('employee_email'), accounting_export.workspace_id)
    except (InvalidTokenError, InternalServerError) as e:
        logger.info('Invalid Fyle refresh token or internal server error for workspace %s: %s', accounting_export.workspace_id, str(e))
        return None

    except Exception as e:
        logger.error('Error syncing inactive employee for workspace_id %s: %s', accounting_export.workspace_id, str(e))
        return None


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
                error, _ = Error.objects.update_or_create(
                    workspace_id=accounting_export.workspace_id,
                    expense_attribute=category_attribute,
                    defaults={
                        'type': 'CATEGORY_MAPPING',
                        'error_title': category_attribute.value,
                        'error_detail': 'Category mapping is missing',
                        'is_resolved': False
                    }
                )

                error.increase_repetition_count_by_one()

        row = row + 1

    return bulk_errors


def __validate_employee_mapping(accounting_export: AccountingExport):

    bulk_errors = []
    row = 0

    employee_email = accounting_export.description.get('employee_email')

    employee_attribute = get_employee_expense_attribute(employee_email, accounting_export.workspace_id)

    if not employee_attribute:
        employee_attribute = sync_inactive_employee(accounting_export)

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
    Error.objects.filter(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, is_resolved=False).update(is_resolved=True, updated_at=datetime.now(timezone.utc))


def validate_failing_export(is_auto_export: bool, interval_hours: int, error: Error):
    """
    Validate failing export
    :param is_auto_export: Is auto export
    :param interval_hours: Interval hours
    :param error: Error
    """
    # If auto export is enabled and interval hours is set and error repetition count is greater than 100, export only once a day
    return is_auto_export and interval_hours and error and error.repetition_count > 100 and datetime.now().replace(tzinfo=timezone.utc) - error.updated_at <= timedelta(hours=24)
