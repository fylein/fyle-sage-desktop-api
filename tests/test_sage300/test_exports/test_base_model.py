from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import AdvancedSetting
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice
from apps.fyle.models import Expense, DependentFieldSetting
from fyle_accounting_mappings.models import (
    ExpenseAttribute,
    Mapping,
    MappingSetting,
    EmployeeMapping
)


def test_base_model_get_invoice_date(
    db,
    create_temp_workspace,
    add_purchase_invoice_objects
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    base_model = PurchaseInvoice

    accounting_export.description = {"spent_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.description = {"approved_at": "2023-04-01T00:00:00"}
    accounting_export.save()
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export.description = {"verified_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export.description = {"last_spent_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export.description = {"posted_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"


def test_get_expense_purpose(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    create_expense_objects,
    add_advanced_settings
):
    workspace_id = 1
    base_model = PurchaseInvoice
    category = 'Food'

    line_item = Expense.objects.filter(workspace_id=workspace_id).first()
    advanced_settings = AdvancedSetting.objects.filter(workspace_id=workspace_id).first()

    return_value = base_model.get_expense_purpose(
        workspace_id=workspace_id,
        lineitem=line_item,
        category=category,
        advance_setting=advanced_settings
    )
    assert return_value == 'Food - jhonsnow@fyle.in'


def test_get_total_amount(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_accounting_export_expenses,
):
    workspace_id = 1
    base_model = PurchaseInvoice

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))

    return_value = base_model.get_total_amount(accounting_export)
    assert return_value == 150.0


def test_get_cost_code_id(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_accounting_export_expenses,
    add_dependent_field_setting,
    add_cost_category
):
    workspace_id = 1
    base_model = PurchaseInvoice

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))

    return_value = base_model.get_cost_code_id(
        accounting_export=accounting_export,
        lineitem=Expense.objects.filter(workspace_id=workspace_id).first(),
        dependent_field_setting=DependentFieldSetting.objects.filter(workspace_id=workspace_id).first(),
        job_id='job_id'
    )

    assert return_value == 'cost_code_id'


def test_get_cost_category_id(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_accounting_export_expenses,
    add_dependent_field_setting,
    add_cost_category
):
    workspace_id = 1
    base_model = PurchaseInvoice

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))

    return_value = base_model.get_cost_category_id(
        accounting_export=accounting_export,
        lineitem=Expense.objects.filter(workspace_id=workspace_id).first(),
        dependent_field_setting=DependentFieldSetting.objects.filter(workspace_id=workspace_id).first(),
        project_id='job_id',
        cost_code_id='cost_code_id'
    )

    assert return_value == 'cost_category_id'


def test_get_vendor_id(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_export_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    base_model = PurchaseInvoice

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))
    accounting_export.fund_source = 'PERSONAL'
    accounting_export.description = {'employee_email': 'ashwin.t@fyle.in'}
    accounting_export.save()

    emp_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()
    emp_mapping.source_employee__value = 'ashwin.t@fyle.in'
    emp_mapping.save()

    return_value = base_model.get_vendor_id(
        accounting_export=accounting_export
    )

    vendor = EmployeeMapping.objects.filter(
        source_employee__value='ashwin.t@fyle.in',
        workspace_id=accounting_export.workspace_id
    ).values_list('destination_vendor__destination_id', flat=True).first()

    assert return_value is not None
    assert return_value == vendor


def test_get_vendor_id_2(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_export_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    base_model = PurchaseInvoice

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))
    accounting_export.fund_source = 'CCC'
    accounting_export.description = {'employee_email': 'ashwin.t@fyle.in'}
    accounting_export.save()

    return_value = base_model.get_vendor_id(
        accounting_export=accounting_export
    )

    assert return_value is not None
    assert return_value == 'dest_vendor123'


def test_get_vendor_id_3(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_export_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    base_model = PurchaseInvoice

    expenses = Expense.objects.filter(workspace_id=workspace_id).first()
    expenses.vendor = None
    expenses.save()

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.fund_source = 'CCC'
    accounting_export.expenses.set([expenses])

    accounting_export.description = {'employee_email': 'ashwin.t@fyle.in'}
    accounting_export.save()

    return_value = base_model.get_vendor_id(
        accounting_export=accounting_export
    )

    assert return_value is not None
    assert return_value == '1'


def test_get_job_id(
    db,
    mocker,
    create_temp_workspace,
    create_expense_objects,
    create_expense_attribute,
    add_accounting_export_expenses,
    create_mapping_object,
    add_import_settings
):
    workspace_id = 1
    base_model = PurchaseInvoice

    mapping_setting = MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='JOB',
        import_to_fyle=False
    )

    expense = Expense.objects.filter(workspace_id=workspace_id).first()
    expense.project = "Op Bandar"
    expense.save()

    mapping = Mapping.objects.filter(workspace_id=workspace_id).first()
    mapping.source_type = 'PROJECT'
    mapping.destination_type = 'JOB'
    mapping.source.value = 'Op Bandar'
    mapping.source.save()
    mapping.save()

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))

    return_value = base_model.get_job_id(
        accounting_export=accounting_export,
        expense=expense
    )

    assert return_value == 'destination123'

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()

    expense.cost_center = 'Op Bandar'
    expense.save()

    mapping.source_type = 'COST_CENTER'
    mapping.save()

    return_value = base_model.get_job_id(
        accounting_export=accounting_export,
        expense=expense
    )

    assert return_value == 'destination123'

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='COST_CODE',
        display_name='Cost Code',
        value='Direct Mail Campaign',
        source_id='10064',
        detail='Sage 300 Project - Direct Mail Campaign, Id - 10064',
        active=True
    )

    mapping_setting.source_field = 'COST_CODE'
    mapping_setting.save()

    mapping.source_type = 'COST_CODE'
    mapping.source.value = 'Direct Mail Campaign'
    mapping.source.save()
    mapping.save()

    return_value = base_model.get_job_id(
        accounting_export=accounting_export,
        expense=expense
    )

    assert return_value == 'destination123'


def test_get_standard_category_id(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_accounting_export_expenses,
    create_mapping_object,
    add_import_settings
):
    workspace_id = 1
    base_model = PurchaseInvoice

    expense = Expense.objects.filter(workspace_id=workspace_id).first()

    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='CATEGORY',
        destination_field='STANDARD_CATEGORY',
        import_to_fyle=False
    )

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        display_name='Cost Code',
        value='Direct Mail Campaign',
        source_id='10064',
        detail='Sage 300 Project - Direct Mail Campaign, Id - 10064',
        active=True
    )

    mapping = Mapping.objects.filter(workspace_id=workspace_id).first()
    mapping.source_type = 'CATEGORY'
    mapping.destination_type = 'STANDARD_CATEGORY'
    mapping.source.value = 'Direct Mail Campaign'
    mapping.source.save()
    mapping.save()

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    return_value = base_model.get_standard_category_id(
        accounting_export=accounting_export,
        expense=expense
    )

    assert return_value == 'destination123'


def test_get_standard_cost_code_id(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_accounting_export_expenses,
    create_mapping_object,
    add_import_settings
):
    workspace_id = 1
    base_model = PurchaseInvoice

    expense = Expense.objects.filter(workspace_id=workspace_id).first()

    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='COST_CODE',
        destination_field='STANDARD_COST_CODE',
        import_to_fyle=False
    )

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='COST_CODE',
        display_name='Cost Code',
        value='Direct Mail Campaign',
        source_id='10064',
        detail='Sage 300 Project - Direct Mail Campaign, Id - 10064',
        active=True
    )

    mapping = Mapping.objects.filter(workspace_id=workspace_id).first()
    mapping.source_type = 'COST_CODE'
    mapping.destination_type = 'STANDARD_COST_CODE'
    mapping.source.value = 'Direct Mail Campaign'
    mapping.source.save()
    mapping.save()

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    return_value = base_model.get_standard_cost_code_id(
        accounting_export=accounting_export,
        expense=expense
    )

    assert return_value == 'destination123'
