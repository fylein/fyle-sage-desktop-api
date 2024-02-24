from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.queues import poll_operation_status
from apps.sage300.exports.direct_cost.queues import poll_operation_status as poll_operation_status_direct_cost


def test_poll_operation_status(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_fyle_credentials,
    add_accounting_export_expenses
):
    """
    function to test poll operation status
    """
    operation_status = {
        "Id": "e0d57177-2700-49a1-a933-b0c900bf1c4e",
        "CreatedOn": "2023-11-29T18:35:48.8712983",
        "TransmittedOn": "2023-11-29T18:35:49.5785546",
        "ReceivedOn": "2023-11-29T18:35:49.7466667",
        "DisabledOn": None,
        "CompletedOn": "2023-11-29T18:36:01.6307696"
    }

    mock_sage_connector = mocker.patch(
        'apps.sage300.exports.purchase_invoice.queues.SageDesktopConnector'
    )

    mock_sage_connector.return_value.connection.operation_status.get.return_value = operation_status
    mock_sage_connector.return_value.update_cookie.return_value = {'text': {'Result': 2}}
    mock_sage_connector.return_value.connection.documents.get.return_value = {
        'CurrentState': '9'
    }
    mock_sage_connector.return_value.connection.event_failures.get.return_value = [
        {
            "CreatedOnUtc": "2023-08-17T09:46:30Z",
            "EntityId": "728406bd-32f6-4676-95ff-b06100a0f840",
            "ErrorMessage": "Exception of type 'DBI.Synchronization.Processing.TimberlineOffice.KeyAlreadyInUseException' was thrown.",
            "Id": "6615abdf-733f-4190-a4ed-b06100a1166f",
            "TypeId": "4de325f1-a380-41cc-90ce-be1e02fef167",
            "Version": 12967
        },
    ]

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE').first()
    assert accounting_export.status == 'EXPORT_QUEUED'

    poll_operation_status(workspace_id=1, last_export=False)

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE').first()
    assert accounting_export.status == 'COMPLETE'

    mock_sage_connector.return_value.connection.documents.get.return_value = {
        'CurrentState': '6'
    }
    accounting_export.status = 'EXPORT_QUEUED'
    accounting_export.save()

    poll_operation_status(workspace_id=1, last_export=False)
    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE')
    assert accounting_export.count() == 1
    assert accounting_export.first().status == 'FAILED'


def test_direct_cost_poll_operation_status(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_fyle_credentials,
    add_accounting_export_expenses
):
    """
    function to test poll operation status
    """
    operation_status = {
        "Id": "e0d57177-2700-49a1-a933-b0c900bf1c4e",
        "CreatedOn": "2023-11-29T18:35:48.8712983",
        "TransmittedOn": "2023-11-29T18:35:49.5785546",
        "ReceivedOn": "2023-11-29T18:35:49.7466667",
        "DisabledOn": "2023-11-29T18:36:01.6307696",
        "CompletedOn": "2023-11-29T18:36:01.6307696"
    }

    mock_sage_connector = mocker.patch(
        'apps.sage300.exports.direct_cost.queues.SageDesktopConnector'
    )

    mock_sage_connector.return_value.connection.operation_status.get.return_value = operation_status
    mock_sage_connector.return_value.update_cookie.return_value = {'text': {'Result': 2}}
    mock_sage_connector.return_value.connection.documents.get.return_value = {
        'CurrentState': '9'
    }
    mock_sage_connector.return_value.connection.event_failures.get.return_value = [
        {
            "CreatedOnUtc": "2023-08-17T09:46:30Z",
            "EntityId": "728406bd-32f6-4676-95ff-b06100a0f840",
            "ErrorMessage": "Exception of type 'DBI.Synchronization.Processing.TimberlineOffice.KeyAlreadyInUseException' was thrown.",
            "Id": "6615abdf-733f-4190-a4ed-b06100a1166f",
            "TypeId": "4de325f1-a380-41cc-90ce-be1e02fef167",
            "Version": 12967
        },
    ]

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST').first()
    assert accounting_export.status == 'EXPORT_QUEUED'

    poll_operation_status_direct_cost(workspace_id=1, last_export=False)

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST').first()
    assert accounting_export.status == 'COMPLETE'

    mock_sage_connector.return_value.connection.documents.get.return_value = {
        'CurrentState': '6'
    }

    accounting_export.status = 'EXPORT_QUEUED'
    accounting_export.save()

    poll_operation_status_direct_cost(workspace_id=1, last_export=False)
    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST')

    assert accounting_export.count() == 1
    assert accounting_export.first().status == 'FAILED'
