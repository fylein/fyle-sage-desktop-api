from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.direct_cost.models import DirectCost
from apps.sage300.exports.direct_cost.tasks import ExportDirectCost, create_direct_cost
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.sage300.exports.purchase_invoice.tasks import ExportPurchaseInvoice, create_purchase_invoice


def test_trigger_export_purchase_invoice(db, mocker):
    '''
    Test trigger_export method of ExportPurchaseInvoice class
    Just for coverage
    '''

    mocker.patch(
        'apps.sage300.exports.purchase_invoice.queues.check_accounting_export_and_start_import'
    )

    export_purchase_invoice = ExportPurchaseInvoice()
    export_purchase_invoice.trigger_export(1, [1], False, 0, ExpenseImportSourceEnum.DIRECT_EXPORT)

    assert True


def test_construct_purchase_invoice(
    db,
    mocker,
    add_import_settings,
    add_purchase_invoice_lineitem_objects
):
    '''
    Test __construct_purchase_invoice method of ExportPurchaseInvoice class
    '''

    workspace_id = 1
    purchase_invoice = PurchaseInvoice.objects.filter(workspace_id=workspace_id).first()
    purchase_invoice.description = {
        'fund_source': 'PERSONAL',
        'employee_email': 'jhonsnow@fyle.in'
    }
    purchase_invoice.save()

    lineitems = PurchaseInvoiceLineitems.objects.filter(workspace_id=workspace_id)

    export_purchase_invoice = ExportPurchaseInvoice()
    payload = export_purchase_invoice.\
        _ExportPurchaseInvoice__construct_purchase_invoice(
            purchase_invoice,
            lineitems
        )

    assert payload['Snapshot']['Header']['Code'] == 'PERSONAL-2'
    assert payload['Snapshot']['Header']['InvoiceDate'] == purchase_invoice.invoice_date


def test_post(
    db,
    mocker,
    add_sage300_creds,
    add_import_settings,
    add_purchase_invoice_lineitem_objects
):
    '''
    Test post method of ExportPurchaseInvoice class
    '''

    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    purchase_invoice = PurchaseInvoice.objects.filter(workspace_id=workspace_id).first()
    lineitems = PurchaseInvoiceLineitems.objects.filter(workspace_id=workspace_id)

    purchase_invoice.description = {
        'fund_source': 'PERSONAL',
        'employee_email': 'jhonsnow@fyle.in'
    }
    purchase_invoice.save()

    export_purchase_invoice = ExportPurchaseInvoice()
    export_purchase_invoice._ExportPurchaseInvoice__construct_purchase_invoice = mocker.MagicMock()
    export_purchase_invoice._ExportPurchaseInvoice__construct_purchase_invoice.return_value = {
        'DocumentTypeId': '76744AB9-4697-430A-ADB5-701E633472A9',
        'Snapshot': {
            'Distributions': [],
            'Header': {
                'AccountingDate': purchase_invoice.invoice_date,
                'Amount': purchase_invoice.amount,
                "Code": '{}-{}'.format(purchase_invoice.description['fund_source'], purchase_invoice.id),
                "Description": purchase_invoice.description['employee_email'],
                "InvoiceDate": purchase_invoice.invoice_date,
                "VendorId": purchase_invoice.vendor_id
            }
        }
    }

    sage300_connection = mocker.MagicMock()

    mocker.patch(
        'apps.sage300.exports.purchase_invoice.tasks.SageDesktopConnector',
        return_value=sage300_connection
    )

    sage300_connection.connection.documents.post_document = mocker.MagicMock()
    sage300_connection.connection.documents.post_document.return_value = '123'

    sage300_connection.connection.documents.export_document = mocker.MagicMock()
    sage300_connection.connection.documents.export_document.return_value = '123'

    exported_purchase_invoice_id = export_purchase_invoice.post(accounting_export, purchase_invoice, lineitems)

    assert exported_purchase_invoice_id == '123'
    assert sage300_connection.connection.documents.post_document.call_count == 1
    assert sage300_connection.connection.documents.export_document.call_count == 1


def test_create_purchase_invoice(
    db,
    mocker,
    add_sage300_creds,
    add_import_settings,
    add_purchase_invoice_lineitem_objects
):
    '''
    Test create_purchase_invoice method of ExportPurchaseInvoice class
    '''

    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    export_purchase = mocker.patch(
        'apps.sage300.exports.purchase_invoice.tasks.ExportPurchaseInvoice',
    )
    mocker.patch.object(
        export_purchase.return_value,
        'create_sage300_object',
        return_value='123'
    )

    exported_purchase_invoice = create_purchase_invoice(accounting_export.id, False)

    assert exported_purchase_invoice == '123'


def test_trigger_export_direct_cost(db, mocker):
    '''
    Test trigger_export method of ExportDirectCost class
    Just for coverage
    '''

    mocker.patch(
        'apps.sage300.exports.direct_cost.queues.check_accounting_export_and_start_import'
    )

    export_direct_cost = ExportDirectCost()
    export_direct_cost.trigger_export(1, [1], False, 0, ExpenseImportSourceEnum.DIRECT_EXPORT)

    assert True


def test_construct_direct_cost(
    db,
    mocker,
    add_import_settings,
    add_direct_cost_objects
):
    '''
    Test __construct_direct_cost method of ExportPurchaseInvoice class
    '''
    workspace_id = 1

    direct_cost = DirectCost.objects.filter(workspace_id=workspace_id).first()

    export_direct_cost = ExportDirectCost()
    payload = export_direct_cost.\
        _ExportDirectCost__construct_direct_cost(
            direct_cost
        )

    assert payload['AccountingDate'] == direct_cost.accounting_date
    assert payload['Amount'] == direct_cost.amount


def test_post_direct_cost(
    db,
    mocker,
    add_sage300_creds,
    add_import_settings,
    add_direct_cost_objects
):
    '''
    Test post method of ExportDirectCost class
    '''

    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    direct_cost = DirectCost.objects.filter(workspace_id=workspace_id).first()

    export_direct_cost = ExportDirectCost()
    export_direct_cost._ExportDirectCost__construct_direct_cost = mocker.MagicMock()
    export_direct_cost._ExportDirectCost__construct_direct_cost.return_value = {
        'AccountingDate': direct_cost.accounting_date,
        'Amount': direct_cost.amount,
        "Code": '{}-{}'.format('REIM', direct_cost.id),
        "Description": direct_cost.description[0:30],
        "TransactionDate": direct_cost.accounting_date,
        "TransactionType": 1
    }

    sage300_connection = mocker.MagicMock()

    mocker.patch(
        'apps.sage300.exports.direct_cost.tasks.SageDesktopConnector',
        return_value=sage300_connection
    )

    sage300_connection.connection.direct_costs.post_direct_cost = mocker.MagicMock()
    sage300_connection.connection.direct_costs.post_direct_cost.return_value = '123'

    sage300_connection.connection.direct_costs.export_direct_cost = mocker.MagicMock()
    sage300_connection.connection.direct_costs.export_direct_cost.return_value = '123'

    exported_direct_cost_id = export_direct_cost.post(accounting_export, direct_cost)

    assert exported_direct_cost_id == '123'
    assert sage300_connection.connection.direct_costs.post_direct_cost.call_count == 1
    assert sage300_connection.connection.direct_costs.export_direct_cost.call_count == 1


def test_create_direct_cost(
    db,
    mocker,
    add_sage300_creds,
    add_import_settings,
    add_direct_cost_objects
):
    '''
    Test create_direct_cost method of ExportDirectCost class
    '''

    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    export_direct_cost = mocker.patch(
        'apps.sage300.exports.direct_cost.tasks.ExportDirectCost',
    )
    mocker.patch.object(
        export_direct_cost.return_value,
        'create_sage300_object',
        return_value='123'
    )

    exported_direct_cost = create_direct_cost(accounting_export.id, False)

    assert exported_direct_cost == '123'
