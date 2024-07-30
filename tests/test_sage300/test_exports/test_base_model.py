from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import AdvancedSetting
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice
from apps.fyle.models import Expense, DependentFieldSetting
from fyle_accounting_mappings.models import (
    ExpenseAttribute,
    DestinationAttribute,
    Mapping,
    MappingSetting,
    EmployeeMapping
)
from apps.workspaces.models import ExportSetting
from apps.accounting_exports.models import _group_expenses
from apps.sage300.models import CostCategory


def test_base_model_get_invoice_date(
    db,
    create_temp_workspace,
    add_purchase_invoice_objects
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    base_model = PurchaseInvoice

    accounting_export.description = {"spent_at": "2023-04-01"}
    return_value = base_model.get_invoice_date(accounting_export)
    assert return_value == "2023-04-01"

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.description = {"approved_at": "2023-04-01"}
    accounting_export.save()
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01"

    accounting_export.description = {"verified_at": "2023-04-01"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01"

    accounting_export.description = {"last_spent_at": "2023-04-01"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01"

    accounting_export.description = {"posted_at": "2023-04-01"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01"


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
        job_id='10081',
        prepend_code_in_name=False
    )

    assert return_value == 'cost_code_id'

    cost_category = CostCategory.objects.create(
        workspace_id=workspace_id,
        job_id='10065',
        cost_code_id='cost_code_id',
        cost_category_id='cost_category_id',
        job_name='Job_Name',
        cost_code_name='Cost_Code_Name',
        name='Cost_Category_Name',
        is_imported=False,
        job_code='Job_Code',
        cost_code_code='Cost_Code',
        cost_category_code='Cost_Category_Code'
    )

    line_item = Expense.objects.filter(workspace_id=workspace_id).first()
    dep_setting = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()

    line_item.custom_properties = {
        dep_setting.cost_code_field_name: 'Cost_Code Cost_Code_Name'
    }
    line_item.save()

    return_value = base_model.get_cost_code_id(
        accounting_export=accounting_export,
        lineitem=line_item,
        dependent_field_setting=dep_setting,
        job_id='10065',
        prepend_code_in_name=True
    )

    assert return_value == cost_category.cost_code_id


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
        project_id='10064',
        cost_code_id='cost_code_id',
        prepend_code_in_name=False
    )

    assert return_value == 'cost_category_id'

    cost_category = CostCategory.objects.create(
        workspace_id=workspace_id,
        job_id='10065',
        cost_code_id='cost_code_id',
        cost_category_id='cost_category_id',
        job_name='Job_Name',
        cost_code_name='Cost_Code_Name',
        name='Cost_Category_Name',
        is_imported=False,
        job_code='Job_Code',
        cost_code_code='Cost_Code',
        cost_category_code='Cost_Category_Code'
    )

    line_item = Expense.objects.filter(workspace_id=workspace_id).first()
    dep_setting = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()

    line_item.custom_properties = {
        dep_setting.cost_category_field_name: 'Cost_Category_Code Cost_Category_Name'
    }
    line_item.save()

    return_value = base_model.get_cost_category_id(
        accounting_export=accounting_export,
        lineitem=line_item,
        dependent_field_setting=dep_setting,
        project_id='10065',
        cost_code_id='cost_code_id',
        prepend_code_in_name=True
    )

    assert return_value == cost_category.cost_category_id


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

    export_settings = ExportSetting.objects.filter(workspace_id=accounting_export.workspace_id).first()

    assert return_value is not None
    assert return_value == export_settings.default_vendor_id


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


def test_get_vendor_id_4(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_export_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    base_model = PurchaseInvoice

    corporate_card, _ = ExpenseAttribute.objects.update_or_create(
        workspace_id=workspace_id,
        defaults = {
            'attribute_type':'CORPORATE_CARD',
            'display_name':'Corporate Card',
            'value':'Bank of Fyle - T1711',
            'source_id':'bankoffyle123',
            'detail': {'cardholder_name': None}
        }
    )

    vendor = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').first()

    Mapping.objects.update_or_create(
        workspace_id=workspace_id,
        defaults = {
            'source_type':'CORPORATE_CARD',
            'destination_type':'VENDOR',
            'source':corporate_card,
            'destination':vendor
        }
    )

    expense = Expense.objects.filter(workspace_id=workspace_id).first()
    expense.fund_source = 'CCC'
    expense.corporate_card_id = corporate_card.source_id
    expense.save()

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.expenses.set([expense])
    accounting_export.fund_source = 'CCC'
    accounting_export.description = {'employee_email': 'ashwin.t@fyle.in'}
    accounting_export.save()

    return_value = base_model.get_vendor_id(
        accounting_export=accounting_export
    )

    assert return_value is not None
    assert return_value == vendor.destination_id


def test_group_expenses(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_export_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1

    corporate_card_x, _ = ExpenseAttribute.objects.update_or_create(
        workspace_id=workspace_id,
        defaults = {
            'attribute_type':'CORPORATE_CARD',
            'display_name':'Corporate Card',
            'value':'Bank of Fyle - X',
            'source_id':'bankoffyle123X',
            'detail': {'cardholder_name': None}
        }
    )

    corporate_card_y, _ = ExpenseAttribute.objects.update_or_create(
        workspace_id=workspace_id,
        defaults = {
            'attribute_type':'CORPORATE_CARD',
            'display_name':'Corporate Card',
            'value':'Bank of Fyle - Y',
            'source_id':'bankoffyle123Y',
            'detail': {'cardholder_name': None}
        }
    )

    vendors = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR')[0:2]

    Mapping.objects.update_or_create(
        workspace_id=workspace_id,
        defaults = {
            'source_type':'CORPORATE_CARD',
            'destination_type':'VENDOR',
            'source':corporate_card_x,
            'destination':vendors[0]
        }
    )

    Mapping.objects.update_or_create(
        workspace_id=workspace_id,
        defaults = {
            'source_type':'CORPORATE_CARD',
            'destination_type':'VENDOR',
            'source':corporate_card_y,
            'destination':vendors[0]
        }
    )

    expenses = []
    for _ in range(3):
        expense = Expense.objects.filter(workspace_id=workspace_id).first()
        expense.pk = None
        expenses.append(expense)

    expenses[0].fund_source = 'CCC'
    expenses[0].expense_id = 'tx4ziVSA124'
    expenses[0].corporate_card_id = None
    expenses[0].save()

    expenses[1].fund_source = 'CCC'
    expenses[1].expense_id = 'tx4ziVSAsfsf'
    expenses[1].corporate_card_id = corporate_card_x.source_id
    expenses[1].save()

    expenses[2].fund_source = 'CCC'
    expenses[2].expense_id = 'tx4zisdAssda'
    expenses[2].corporate_card_id = corporate_card_y.source_id
    expenses[2].save()

    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()
    export_settings.credit_card_expense_grouped_by = 'REPORT'
    export_settings.credit_card_expense_date = 'POSTED_AT'
    export_settings.reimbursable_expense_grouped_by = 'REPORT'
    export_settings.reimbursable_expense_date = 'PAYMENT_PROCESSING'
    export_settings.save()

    accounting_export = _group_expenses(expenses=expenses, export_setting=export_settings, fund_source='CCC')
    assert len(accounting_export) == 3


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
