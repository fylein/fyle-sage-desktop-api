from apps.sage300.exports.helpers import (
    get_employee_expense_attribute,
    get_filtered_mapping,
    __validate_category_mapping,
    __validate_employee_mapping,
    validate_accounting_export,
    resolve_errors_for_exported_accounting_export,
    get_valid_date_format
)
from fyle_accounting_mappings.models import (
    CategoryMapping,
    EmployeeMapping,
    ExpenseAttribute,
    Mapping
)
from apps.accounting_exports.models import AccountingExport, Error
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
    assert error.error_detail == 'Employee mapping is missing'
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
    assert error.error_detail == 'Category mapping is missing'
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


def test_get_valid_date_format():
    valid_date_format = get_valid_date_format('2024-05-21')
    assert valid_date_format == '2024-05-21'

    valid_date_format = get_valid_date_format('2024-05-21T17:11:00')
    assert valid_date_format == '2024-05-21'
