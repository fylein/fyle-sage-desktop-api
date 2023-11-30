import pytest  # noqa
from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.queues import poll_operation_status
from apps.sage300.exports.direct_cost.queues import poll_operation_status as poll_operation_status_direct_cost


def test_poll_operation_status(test_connection, mocker, create_temp_workspace, add_sage300_creds, add_fyle_credentials, add_accounting_export_expenses):
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

    mocker.patch(
        'sage_desktop_sdk.core.client.Client.update_cookie',
        return_value={'text': {'Result': 2}}
    )

    mocker.patch(
        'sage_desktop_sdk.apis.OperationStatus.get',
        return_value=operation_status
    )

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE').first()
    assert accounting_export.status == 'EXPORT_QUEUED'

    poll_operation_status(workspace_id=1)

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE').first()
    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.detail == operation_status

    operation_status = {
        "Id": "e0d57177-2700-49a1-a933-b0c900bf1c4e",
        "CreatedOn": "2023-11-29T18:35:48.8712983",
        "TransmittedOn": "2023-11-29T18:35:49.5785546",
        "ReceivedOn": "2023-11-29T18:35:49.7466667",
        "DisabledOn": "2023-11-29T18:36:01.6307696",
        "CompletedOn": "2023-11-29T18:36:01.6307696"
    }

    mocker.patch(
        'sage_desktop_sdk.apis.EventFaliure.get',
        return_value=[
            {
                "CreatedOnUtc": "2023-08-17T09:46:30Z",
                "EntityId": "728406bd-32f6-4676-95ff-b06100a0f840",
                "ErrorMessage": "Exception of type 'DBI.Synchronization.Processing.TimberlineOffice.KeyAlreadyInUseException' was thrown.",
                "Id": "6615abdf-733f-4190-a4ed-b06100a1166f",
                "TypeId": "4de325f1-a380-41cc-90ce-be1e02fef167",
                "Version": 12967
            },
        ]
    )

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST').first()
    assert accounting_export.status == 'EXPORT_QUEUED'

    poll_operation_status_direct_cost(workspace_id=1)
    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST').first()
    accounting_export.status == 'FAILED'
