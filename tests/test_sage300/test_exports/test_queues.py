from datetime import datetime

from django_q.models import Schedule
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.accounting_exports.models import AccountingExport, Error
from apps.sage300.exports.direct_cost.queues import (
    check_accounting_export_and_start_import as check_accounting_export_and_start_import_direct_cost,
)
from apps.sage300.exports.direct_cost.queues import create_schedule_for_polling as create_schedule_for_polling_direct_cost
from apps.sage300.exports.direct_cost.queues import poll_operation_status as poll_operation_status_direct_cost
from apps.sage300.exports.direct_cost.queues import trigger_poll_operation_status as trigger_poll_operation_status_direct_cost
from apps.sage300.exports.purchase_invoice.queues import (
    check_accounting_export_and_start_import,
    create_schedule_for_polling,
    poll_operation_status,
    trigger_poll_operation_status,
)
from workers.helpers import WorkerActionEnum, RoutingKeyEnum


def test_poll_operation_status_purchase_invoice_publishes_to_rabbitmq(
    db,
    mocker,
    create_temp_workspace
):
    """Test that poll_operation_status publishes the correct payload to RabbitMQ"""
    mock_publish = mocker.patch('apps.sage300.exports.purchase_invoice.queues.publish_to_rabbitmq')

    poll_operation_status(workspace_id=1)

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args[1]
    assert call_kwargs['payload']['workspace_id'] == 1
    assert call_kwargs['payload']['action'] == WorkerActionEnum.POLL_PURCHASE_INVOICE_STATUS.value
    assert call_kwargs['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


def test_trigger_poll_operation_status_purchase_invoice(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_fyle_credentials,
    add_accounting_export_expenses
):
    """
    Test trigger_poll_operation_status for purchase invoice
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

    trigger_poll_operation_status(workspace_id=1)

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE').first()
    assert accounting_export.status == 'COMPLETE'

    mock_sage_connector.return_value.connection.documents.get.return_value = {
        'CurrentState': '6'
    }
    accounting_export.status = 'EXPORT_QUEUED'
    accounting_export.save()

    trigger_poll_operation_status(workspace_id=1)
    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE')
    assert accounting_export.count() == 1
    assert accounting_export.first().status == 'FAILED'


def test_check_accounting_export_and_start_import_purchase_invoice(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    mocker
):
    """
    Test check_accounting_export_and_start_import for purchase invoice
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='PURCHASE_INVOICE').first()
    accounting_export.status = 'ENQUEUED'
    accounting_export.exported_at = None
    accounting_export.save()

    mocker.patch('apps.sage300.exports.purchase_invoice.tasks.create_purchase_invoice')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'PURCHASE_INVOICE'

    accounting_export.status = 'COMPLETE'
    accounting_export.save()

    check_accounting_export_and_start_import(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.type == 'PURCHASE_INVOICE'


def test_create_schedule_for_polling_purchase_invoice(
    db,
):
    """
    Test create_schedule_for_polling
    """
    create_schedule_for_polling(workspace_id=1)
    create_schedule_for_polling(workspace_id=1)

    schedule = Schedule.objects.filter(
        func='apps.sage300.exports.purchase_invoice.queues.poll_operation_status',
        args='1'
    ).first()

    assert schedule is not None

    schedule = Schedule.objects.filter(
        func='apps.sage300.exports.purchase_invoice.queues.poll_operation_status',
        args='1'
    ).first()

    assert schedule is not None


def test_poll_operation_status_direct_cost_publishes_to_rabbitmq(
    db,
    mocker,
    create_temp_workspace
):
    """Test that poll_operation_status publishes the correct payload to RabbitMQ"""
    mock_publish = mocker.patch('apps.sage300.exports.direct_cost.queues.publish_to_rabbitmq')

    poll_operation_status_direct_cost(workspace_id=1)

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args[1]
    assert call_kwargs['payload']['workspace_id'] == 1
    assert call_kwargs['payload']['action'] == WorkerActionEnum.POLL_DIRECT_COST_STATUS.value
    assert call_kwargs['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


def test_trigger_poll_operation_status_direct_cost(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_fyle_credentials,
    add_accounting_export_expenses
):
    """
    Test trigger_poll_operation_status for direct cost
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

    trigger_poll_operation_status_direct_cost(workspace_id=1)

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST').first()
    assert accounting_export.status == 'COMPLETE'

    mock_sage_connector.return_value.connection.documents.get.return_value = {
        'CurrentState': '6'
    }

    accounting_export.status = 'EXPORT_QUEUED'
    accounting_export.save()

    trigger_poll_operation_status_direct_cost(workspace_id=1)
    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='DIRECT_COST')

    assert accounting_export.count() == 1
    assert accounting_export.first().status == 'FAILED'


def test_check_accounting_export_and_start_import_direct_cost(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    mocker
):
    """
    Test check_accounting_export_and_start_import for purchase invoice
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='DIRECT_COST').first()
    accounting_export.status = 'ENQUEUED'
    accounting_export.exported_at = None
    accounting_export.save()

    mocker.patch('apps.sage300.exports.direct_cost.tasks.create_direct_cost')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_direct_cost(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'DIRECT_COST'

    accounting_export.status = 'COMPLETE'
    accounting_export.save()

    check_accounting_export_and_start_import_direct_cost(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.type == 'DIRECT_COST'


def test_create_schedule_for_polling_direct_cost(
    db,
):
    """
    Test create_schedule_for_polling
    """
    create_schedule_for_polling_direct_cost(workspace_id=1)
    create_schedule_for_polling_direct_cost(workspace_id=1)

    schedule = Schedule.objects.filter(
        func='apps.sage300.exports.direct_cost.queues.poll_operation_status',
        args='1'
    ).first()

    assert schedule is not None

    schedule = Schedule.objects.filter(
        func='apps.sage300.exports.direct_cost.queues.poll_operation_status',
        args='1'
    ).first()

    assert schedule is not None


def test_skipping_direct_cost(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    add_feature_config,
    mocker
):
    """
    Test check_accounting_export_and_start_import for purchase invoice
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='DIRECT_COST').first()
    accounting_export.status = ''
    accounting_export.exported_at = None
    accounting_export.save()

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).delete()

    error = Error.objects.create(
        workspace_id=workspace_id,
        type='NETSUITE_ERROR',
        error_title='NetSuite System Error',
        error_detail='An error occured in a upsert request: Please enter value(s) for: Location',
        accounting_export=accounting_export,
        repetition_count=106
    )

    mocker.patch('apps.sage300.exports.direct_cost.tasks.create_direct_cost')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_direct_cost(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == ''
    assert accounting_export.type == 'DIRECT_COST'

    Error.objects.filter(id=error.id).update(updated_at=datetime(2024, 8, 20))

    check_accounting_export_and_start_import_direct_cost(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'DIRECT_COST'


def test_skipping_purchase_invoice(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    add_feature_config,
    mocker
):
    """
    Test check_accounting_export_and_start_import for purchase invoice
    """
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='PURCHASE_INVOICE').first()
    accounting_export.status = ''
    accounting_export.exported_at = None
    accounting_export.save()

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).delete()

    error = Error.objects.create(
        workspace_id=workspace_id,
        type='NETSUITE_ERROR',
        error_title='NetSuite System Error',
        error_detail='An error occured in a upsert request: Please enter value(s) for: Location',
        accounting_export=accounting_export,
        repetition_count=106
    )

    mocker.patch('apps.sage300.exports.purchase_invoice.tasks.create_purchase_invoice')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )
    accounting_export.refresh_from_db()
    assert accounting_export.status == ''
    assert accounting_export.type == 'PURCHASE_INVOICE'

    Error.objects.filter(id=error.id).update(updated_at=datetime(2024, 8, 20))

    check_accounting_export_and_start_import(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )
    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'PURCHASE_INVOICE'


def test_check_accounting_export_with_rabbitmq_worker_purchase_invoice(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    add_feature_config,
    mocker
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='PURCHASE_INVOICE').first()
    accounting_export.status = 'READY'
    accounting_export.exported_at = None
    accounting_export.save()

    mock_check_interval = mocker.patch('apps.sage300.exports.purchase_invoice.queues.check_interval_and_sync_dimension')
    mock_task_executor = mocker.patch('apps.sage300.exports.purchase_invoice.queues.TaskChainRunner')

    check_accounting_export_and_start_import(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.WEBHOOK,
        run_in_rabbitmq_worker=True
    )

    mock_check_interval.assert_called_once_with(workspace_id)
    mock_task_executor.assert_called()


def test_check_accounting_export_with_rabbitmq_worker_direct_cost(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    add_feature_config,
    mocker
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='DIRECT_COST').first()
    accounting_export.status = 'READY'
    accounting_export.exported_at = None
    accounting_export.save()

    mock_check_interval = mocker.patch('apps.sage300.exports.direct_cost.queues.check_interval_and_sync_dimension')
    mock_task_executor = mocker.patch('apps.sage300.exports.direct_cost.queues.TaskChainRunner')

    check_accounting_export_and_start_import_direct_cost(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.WEBHOOK,
        run_in_rabbitmq_worker=True
    )

    mock_check_interval.assert_called_once_with(workspace_id)
    mock_task_executor.assert_called()


def test_skip_export_with_mapping_errors_purchase_invoice(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    add_feature_config,
    mocker
):
    """
    Test that exports are skipped when accounting export has mapping errors
    """
    from fyle_accounting_mappings.models import ExpenseAttribute

    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='PURCHASE_INVOICE').first()
    accounting_export.status = 'READY'
    accounting_export.exported_at = None
    accounting_export.save()

    category_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        value='Unmapped Category',
        display_name='Unmapped Category',
        active=True
    )

    Error.objects.create(
        workspace_id=workspace_id,
        type='CATEGORY_MAPPING',
        expense_attribute=category_attribute,
        mapping_error_accounting_export_ids=[accounting_export.id],
        error_title='Unmapped Category',
        error_detail='Category mapping is missing',
        is_resolved=False
    )

    mocker.patch('apps.sage300.exports.purchase_invoice.tasks.create_purchase_invoice')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mock_chain_run = mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()
    assert accounting_export.status == 'READY'
    mock_chain_run.assert_not_called()


def test_skip_export_with_mapping_errors_direct_cost(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_accounting_export_expenses,
    add_feature_config,
    mocker
):
    """
    Test that exports are skipped when accounting export has mapping errors
    """
    from fyle_accounting_mappings.models import ExpenseAttribute

    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id, type='DIRECT_COST').first()
    accounting_export.status = 'READY'
    accounting_export.exported_at = None
    accounting_export.save()

    category_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        value='Unmapped Category DC',
        display_name='Unmapped Category DC',
        active=True
    )

    Error.objects.create(
        workspace_id=workspace_id,
        type='CATEGORY_MAPPING',
        expense_attribute=category_attribute,
        mapping_error_accounting_export_ids=[accounting_export.id],
        error_title='Unmapped Category DC',
        error_detail='Category mapping is missing',
        is_resolved=False
    )

    mocker.patch('apps.sage300.exports.direct_cost.tasks.create_direct_cost')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mock_chain_run = mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_direct_cost(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0,
        ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    accounting_export.refresh_from_db()
    assert accounting_export.status == 'READY'
    mock_chain_run.assert_not_called()
