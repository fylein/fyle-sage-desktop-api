from fyle.platform.exceptions import InvalidTokenError
from fyle_accounting_mappings.models import CategoryMapping, EmployeeMapping, ExpenseAttribute, Mapping

from apps.accounting_exports.models import AccountingExport, Error
from apps.sage300.exports.helpers import (
    __validate_category_mapping,
    __validate_employee_mapping,
    get_employee_expense_attribute,
    get_filtered_mapping,
    resolve_errors_for_exported_accounting_export,
    sync_inactive_employee,
    validate_accounting_export,
)
from sage_desktop_api.exceptions import BulkError


def test_get_employee_expense_attribute(
    db,
    mocker,
    create_temp_workspace,
    create_expense_attribute
):
    workspace_id = 1
    value = 'ashwin.t@fyle.in'

    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()

    expense_attribute_response = get_employee_expense_attribute(value=value, workspace_id=workspace_id)

    assert expense_attribute_response.value == expense_attribute.value
    assert expense_attribute_response.workspace_id == expense_attribute.workspace_id
    assert expense_attribute_response.attribute_type == expense_attribute.attribute_type
    assert expense_attribute_response.display_name == expense_attribute.display_name


def test_resolve_errors_for_exported_accounting_export(
    db,
    create_temp_workspace,
    add_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id = workspace_id).first()
    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()

    Error.objects.create(
        workspace_id=workspace_id,
        type='EMPLOYEE_MAPPING',
        accounting_export=accounting_export,
        expense_attribute=expense_attribute,
        is_resolved=False,
        error_title='Employee Mapping error',
        error_detail='Employee Mapping error detail'
    )

    resolve_errors_for_exported_accounting_export(accounting_export=accounting_export)

    error = Error.objects.filter(workspace_id=workspace_id).first()

    assert error.is_resolved == True
    assert error.error_title == 'Employee Mapping error'
    assert error.error_detail == 'Employee Mapping error detail'
    assert error.type == 'EMPLOYEE_MAPPING'


def test_get_filtered_mapping(
    db,
    create_temp_workspace,
    create_mapping_object
):
    workspace_id = 1
    mapping = Mapping.objects.filter(workspace_id=workspace_id).first()

    filtered_mapping = get_filtered_mapping(
        source_field="EMPLOYEE",
        destination_type="EMPLOYEE",
        workspace_id=workspace_id,
        source_id="source123",
        source_value="ashwin.t@fyle.in"
    )

    assert filtered_mapping.source_type == mapping.source_type
    assert filtered_mapping.destination_type == mapping.destination_type
    assert filtered_mapping.workspace_id == mapping.workspace_id
    assert filtered_mapping.source.source_id == mapping.source.source_id
    assert filtered_mapping.source.value == mapping.source.value


def test_validate_employee_mapping_1(
    db,
    create_temp_workspace,
    create_employee_mapping_with_employee,
    add_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.description = {
        'employee_email': 'ashwin.t@fyle.in'
    }
    accounting_export.save()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export
    )

    employee_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()

    assert employee_mapping.source_employee.source_id == 'source123'
    assert len(bulk_errors) == 0


def test_validate_employee_mapping_2(
    db,
    create_temp_workspace,
    add_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.description = {
        'employee_email': 'ashwin.t@fyle.in'
    }
    accounting_export.save()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export
    )

    assert len(bulk_errors) == 1
    assert bulk_errors[0]['value'] == 'ashwin.t@fyle.in'
    assert bulk_errors[0]['type'] == 'Employee Mapping'
    assert bulk_errors[0]['message'] == 'Employee Mapping not found'


def test_validate_employee_mapping_3(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    create_employee_mapping_with_employee
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    employee_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()

    accounting_export.description = {
        'employee_email': 'ashwin.t@fyle.in'
    }
    accounting_export.save()

    employee_mapping.delete()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export
    )

    error = Error.objects.filter(workspace_id=workspace_id).first()

    assert len(bulk_errors) == 1
    assert bulk_errors[0]['value'] == 'ashwin.t@fyle.in'
    assert bulk_errors[0]['type'] == 'Employee Mapping'
    assert bulk_errors[0]['message'] == 'Employee Mapping not found'

    assert error.type == 'EMPLOYEE_MAPPING'
    assert 'mapping is missing' in error.error_detail
    assert error.is_resolved == False


def test_validate_employee_mapping_4(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    accounting_export.description = {
        'employee_email': 'ashwin.t@fyle.in'
    }
    accounting_export.save()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export
    )

    employee_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()

    assert employee_mapping.source_employee.source_id == 'source123'
    assert len(bulk_errors) == 0


def test_validate_category_mapping_1(
    db,
    create_temp_workspace,
    create_category_mapping,
    add_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    bulk_errors = __validate_category_mapping(accounting_export)

    category_mapping = CategoryMapping.objects.filter(workspace_id=workspace_id).first()

    assert category_mapping.source_category.attribute_type == 'CATEGORY'
    assert len(bulk_errors) == 0


def test_validate_category_mapping_2(
    db,
    create_temp_workspace,
    create_expense_attribute,
    add_accounting_export_expenses,
    create_category_mapping,
    create_expense_objects
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(create_expense_objects)
    accounting_export.save()

    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()
    expense_attribute.attribute_type = 'CATEGORY'
    expense_attribute.value = 'Accounts Payable'
    expense_attribute.display_name = 'Accounts Payable'
    expense_attribute.save()

    category_mapping = CategoryMapping.objects.filter(workspace_id=workspace_id).first()
    category_mapping.delete()

    bulk_errors = __validate_category_mapping(accounting_export)

    error = Error.objects.filter(workspace_id=workspace_id).first()

    assert len(bulk_errors) == 1
    assert bulk_errors[0]['value'] == 'Accounts Payable'
    assert bulk_errors[0]['type'] == 'Category Mapping'
    assert bulk_errors[0]['message'] == 'Category Mapping not found'

    assert error.type == 'CATEGORY_MAPPING'
    assert 'mapping is missing' in error.error_detail
    assert error.is_resolved == False


def test_validate_accounting_export(
    db,
    mocker,
    create_temp_workspace,
    add_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    mocker.patch(
        'apps.sage300.exports.helpers.__validate_employee_mapping',
        return_value={
            'row': 0,
            'id': 'Random Id',
            'error': 'Dummy Error',
            'type': 'Employee Mapping',
        }
    )
    mocker.patch(
        'apps.sage300.exports.helpers.__validate_category_mapping',
        return_value={
            'row': 0,
            'id': 'Random Id',
            'error': 'Dummy Error',
            'type': 'Category Mapping',
        }
    )

    try:
        validate_accounting_export(
            accounting_export=accounting_export
        )
    except BulkError as e:
        assert str(e) == "'Mappings are missing'"


def test_get_or_create_error_with_accounting_export_creates_new(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_category_expense_attribute
):
    """
    Test get_or_create_error_with_accounting_export creates a new error
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').first()

    error, created = Error.get_or_create_error_with_accounting_export(
        accounting_export=accounting_export,
        expense_attribute=expense_attribute
    )

    assert created is True
    assert error.type == 'CATEGORY_MAPPING'
    assert error.error_detail == f'{expense_attribute.display_name} mapping is missing'
    assert error.error_title == expense_attribute.value
    assert error.is_resolved is False
    assert accounting_export.id in error.mapping_error_accounting_export_ids


def test_get_or_create_error_with_accounting_export_adds_export_id(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_category_mapping_error
):
    """
    Test get_or_create_error_with_accounting_export adds accounting_export.id to existing error
    """
    workspace_id = 1
    accounting_exports = AccountingExport.objects.filter(workspace_id=workspace_id)[:2]
    first_export = accounting_exports[0]
    second_export = accounting_exports[1]

    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').first()
    error = Error.objects.filter(workspace_id=workspace_id, type='CATEGORY_MAPPING').first()
    error.mapping_error_accounting_export_ids = [first_export.id]
    error.save(update_fields=['mapping_error_accounting_export_ids'])

    error, created = Error.get_or_create_error_with_accounting_export(
        accounting_export=second_export,
        expense_attribute=expense_attribute
    )

    assert created is False
    assert first_export.id in error.mapping_error_accounting_export_ids
    assert second_export.id in error.mapping_error_accounting_export_ids


def test_get_or_create_error_with_accounting_export_reopens_resolved(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_category_mapping_error
):
    """
    Test get_or_create_error_with_accounting_export reopens a resolved error
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').first()
    error = Error.objects.filter(workspace_id=workspace_id, type='CATEGORY_MAPPING').first()
    error.is_resolved = True
    error.save(update_fields=['is_resolved'])

    error, created = Error.get_or_create_error_with_accounting_export(
        accounting_export=accounting_export,
        expense_attribute=expense_attribute
    )

    assert created is False
    assert error.is_resolved is False
    assert accounting_export.id in error.mapping_error_accounting_export_ids


def test_get_or_create_error_with_accounting_export_no_update_needed(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_category_mapping_error
):
    """
    Test get_or_create_error_with_accounting_export when no update is needed
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').first()
    error = Error.objects.filter(workspace_id=workspace_id, type='CATEGORY_MAPPING').first()
    error.mapping_error_accounting_export_ids = [accounting_export.id]
    error.save(update_fields=['mapping_error_accounting_export_ids'])

    error, created = Error.get_or_create_error_with_accounting_export(
        accounting_export=accounting_export,
        expense_attribute=expense_attribute
    )

    assert created is False
    assert error.is_resolved is False
    assert error.mapping_error_accounting_export_ids == [accounting_export.id]


def test_sync_inactive_employee(
    db,
    mocker,
    create_temp_workspace,
    add_accounting_export_expenses,
    create_expense_attribute
):
    """
    Test sync_inactive_employee
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.description = {'employee_email': 'inactive_user@fyle.in'}
    accounting_export.save()

    mock_fyle_employee = [{
        'id': 'ouHnjo38H12',
        'user_id': 'usabcdef1234',
        'user': {'email': 'inactive_user@fyle.in', 'full_name': 'Inactive User'},
        'code': 'EMP001',
        'is_enabled': False,
        'has_accepted_invite': True,
        'location': 'San Francisco',
        'department': {'name': 'Engineering', 'code': 'ENG'},
        'department_id': 'deptHnjo38H12'
    }]

    mocker.patch('apps.sage300.exports.helpers.FyleCredential.objects.get')
    mock_platform = mocker.patch('apps.sage300.exports.helpers.PlatformConnector')
    mock_platform.return_value.employees.get_employee_by_email.return_value = mock_fyle_employee
    mocker.patch('apps.sage300.exports.helpers.ExpenseAttribute.bulk_create_or_update_expense_attributes')

    ExpenseAttribute.objects.filter(attribute_type='EMPLOYEE', value='inactive_user@fyle.in', workspace_id=workspace_id).delete()
    ExpenseAttribute.objects.create(workspace_id=workspace_id, attribute_type='EMPLOYEE', display_name='Employee', value='inactive_user@fyle.in', source_id='ouHnjo38H12', active=False)

    result = sync_inactive_employee(accounting_export)
    assert result is not None
    assert result.value == 'inactive_user@fyle.in'

    # InvalidTokenError path
    mocker.patch('apps.sage300.exports.helpers.FyleCredential.objects.get', side_effect=InvalidTokenError('Invalid token'))
    assert sync_inactive_employee(accounting_export) is None

    # Generic exception path
    mocker.patch('apps.sage300.exports.helpers.FyleCredential.objects.get', side_effect=ValueError('bad value'))
    assert sync_inactive_employee(accounting_export) is None
