from datetime import datetime, timedelta

from django.conf import settings
from django.urls import reverse
from django_q.models import Schedule
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.workspaces.models import AdvancedSetting, ExportSetting, FyleCredential
from apps.workspaces.tasks import (
    async_create_admin_subcriptions,
    async_update_fyle_credentials,
    export_to_sage300,
    run_import_export,
    schedule_sync,
)


def test_async_update_fyle_credentials(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    workspace_id = 1
    org_id = "riseabovehate1"

    async_update_fyle_credentials(
        fyle_org_id=org_id,
        refresh_token="refresh_token"
    )

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    assert fyle_credentials.refresh_token == "refresh_token"


def test_run_import_export_with_reimbursable_expense(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses
):
    workspace_id = 1
    AccountingExportSummary.objects.create(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    accounting_export.status = 'COMPLETE'
    accounting_export.fund_source = 'PERSONAL'
    accounting_export.type = 'FETCHING_REIMBURSABLE_EXPENSES'
    accounting_export.exported_at = None
    accounting_export.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_purchase_invoice = mocker.patch('apps.sage300.exports.purchase_invoice.tasks.ExportPurchaseInvoice')
    mocker.patch.object(
        mock_export_purchase_invoice.return_value,
        'trigger_export'
    )

    run_import_export(workspace_id=workspace_id)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES'
    ).first()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'PERSONAL'
    assert accounting_export.type == 'FETCHING_REIMBURSABLE_EXPENSES'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None


def test_run_import_export_with_credit_card_expense(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses
):
    workspace_id = 1
    AccountingExportSummary.objects.create(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        type='FETCHING_CREDIT_CARD_EXPENSES'
    ).first()

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = None
    export_settings.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_settings.save()

    accounting_export.status = 'COMPLETE'
    accounting_export.fund_source = 'CCC'
    accounting_export.exported_at = None
    accounting_export.save()

    mocker.patch('apps.workspaces.tasks.queue_import_credit_card_expenses')
    mock_export_purchase_invoice = mocker.patch('apps.sage300.exports.purchase_invoice.tasks.ExportPurchaseInvoice')
    mocker.patch.object(
        mock_export_purchase_invoice.return_value,
        'trigger_export'
    )

    run_import_export(workspace_id=workspace_id)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        type='FETCHING_CREDIT_CARD_EXPENSES'
    ).first()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'CCC'
    assert accounting_export.type == 'FETCHING_CREDIT_CARD_EXPENSES'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None


def test_sync_schedule(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings
):
    workspace_id = 1

    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advance_settings.schedule_is_enabled = True
    advance_settings.is_real_time_export_enabled = False
    advance_settings.save()

    advanced_settings = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=5,
        email_added=['test2@fyle.in', 'test2@fyle.in'],
        emails_selected=['test1@fyle.in']
    )

    schedule = Schedule.objects.filter(
        args=f'{workspace_id}',
        func='apps.workspaces.tasks.run_import_export'
    ).first()

    assert schedule is not None
    assert advanced_settings.schedule_is_enabled == True
    assert advanced_settings.emails_selected == ['test1@fyle.in']
    assert advanced_settings.interval_hours == 5


def test_sync_schedule_2(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings
):
    workspace_id = 1

    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advance_settings.schedule_is_enabled = True
    advance_settings.save()

    schedules = Schedule.objects.filter(
        args=f'{workspace_id}',
        func='apps.workspaces.tasks.run_import_export',
    )

    assert schedules.count() == 0

    sch, _ = Schedule.objects.update_or_create(
        func='apps.workspaces.tasks.run_import_export',
        args='{}'.format(workspace_id),
        defaults={
            'schedule_type': Schedule.MINUTES,
            'minutes': 5 * 60,
            'next_run': datetime.now() + timedelta(hours=5)
        }
    )

    advance_settings.schedule = sch
    advance_settings.save()

    advanced_settings = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=5,
        email_added=['test2@fyle.in', 'test2@fyle.in'],
        emails_selected=['test1@fyle.in']
    )

    schedules = Schedule.objects.filter(
        args=f'{workspace_id}',
        func='apps.workspaces.tasks.run_import_export',
    )

    assert schedules.count() == 0
    assert schedules.first() is None
    assert advanced_settings.schedule_is_enabled == False


def test_sync_schedule_3(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings
):
    workspace_id = 1

    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advance_settings.schedule_is_enabled = True
    advance_settings.is_real_time_export_enabled = True
    advance_settings.save()

    advanced_settings = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=0,
        email_added=['test2@fyle.in', 'test2@fyle.in'],
        emails_selected=['test1@fyle.in']
    )

    assert advanced_settings.schedule_is_enabled == True
    assert advanced_settings.emails_selected == ['test1@fyle.in']
    assert advanced_settings.interval_hours == 0
    assert advance_settings.is_real_time_export_enabled == True


def test_export_to_sage300(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses
):
    workspace_id = 1
    AccountingExportSummary.objects.create(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'DIRECT_COST'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    accounting_export.status = 'COMPLETE'
    accounting_export.fund_source = 'PERSONAL'
    accounting_export.exported_at = None
    accounting_export.save()

    mock_export_direct_cost = mocker.patch('apps.sage300.exports.direct_cost.tasks.DirectCost')
    mock_export_purchase_invoice = mocker.patch('apps.sage300.exports.purchase_invoice.tasks.ExportPurchaseInvoice')
    mocker.patch.object(
        mock_export_direct_cost.return_value,
        'trigger_export'
    )
    mocker.patch.object(
        mock_export_purchase_invoice.return_value,
        'trigger_export'
    )

    export_to_sage300(workspace_id=workspace_id, triggered_by=ExpenseImportSourceEnum.DIRECT_EXPORT)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id,
    ).first()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'PERSONAL'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None

    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.save()

    export_to_sage300(workspace_id=workspace_id, triggered_by=ExpenseImportSourceEnum.DIRECT_EXPORT)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'PERSONAL'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None


def test_async_create_admin_subcriptions(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    mock_api = mocker.patch(
        'fyle.platform.apis.v1.admin.Subscriptions.post',
        return_value={}
    )
    workspace_id = 1
    async_create_admin_subcriptions(workspace_id=workspace_id)

    payload = {
        'is_enabled': True,
        'webhook_url': '{}/workspaces/{}/fyle/webhook_callback/'.format(settings.API_URL, workspace_id)
    }

    assert mock_api.once_called_with(payload)

    mock_api.side_effect = Exception('Error')
    try:
        async_create_admin_subcriptions(workspace_id=workspace_id)
    except Exception as e:
        assert str(e) == 'Error'


def test_async_create_admin_subcriptions_2(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    mock_api = mocker.patch(
        'fyle.platform.apis.v1.admin.Subscriptions.post',
        return_value={}
    )
    workspace_id = 1
    reverse('webhook-callback', kwargs={'workspace_id': workspace_id})

    payload = {
        'is_enabled': True,
        'webhook_url': '{}/workspaces/{}/fyle/webhook_callback/'.format(settings.API_URL, workspace_id)
    }

    assert mock_api.once_called_with(payload)

    mock_api.side_effect = Exception('Error')
    reverse('webhook-callback', kwargs={'workspace_id': workspace_id})


def test_run_import_export_exclude_failed_exports_reimbursable(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_accounting_export_summary,
    setup_complete_fetching_export,
    clean_slate_exports,
    mixed_retry_exports
):
    """
    Test run_import_export excludes failed reimbursable exports with re_attempt_export=False
    """
    workspace_id = 1

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice', return_value=mock_export_instance)

    run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_called_once()
    call_args = mock_export_instance.trigger_export.call_args
    accounting_export_ids = call_args[1]['accounting_export_ids']

    # Should include EXPORT_READY and FAILED with retry=True, exclude FAILED with retry=False
    ready_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='EXPORT_READY')
    retry_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='FAILED', re_attempt_export=True)
    failed_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='FAILED', re_attempt_export=False)

    expected_ids = [ready_export.id, retry_export.id]
    assert set(accounting_export_ids) == set(expected_ids)
    assert failed_export.id not in accounting_export_ids

    # Verify excluded export remains unchanged
    failed_export.refresh_from_db()
    assert failed_export.status == 'FAILED'
    assert failed_export.re_attempt_export == False


def test_run_import_export_exclude_failed_exports_credit_card(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_accounting_export_summary,
    setup_complete_fetching_export,
    clean_slate_exports,
    mixed_retry_exports
):
    """
    Test run_import_export excludes failed credit card exports with re_attempt_export=False
    """
    workspace_id = 1

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = None
    export_settings.credit_card_expense_export_type = 'DIRECT_COST'
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_credit_card_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportDirectCost', return_value=mock_export_instance)

    run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_called_once()
    call_args = mock_export_instance.trigger_export.call_args
    accounting_export_ids = call_args[1]['accounting_export_ids']

    # Should include EXPORT_READY and FAILED with retry=True, exclude FAILED with retry=False
    ready_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='CCC', status='EXPORT_READY')
    retry_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='CCC', status='FAILED', re_attempt_export=True)
    failed_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='CCC', status='FAILED', re_attempt_export=False)

    expected_ids = [ready_export.id, retry_export.id]
    assert set(accounting_export_ids) == set(expected_ids)
    assert failed_export.id not in accounting_export_ids

    # Verify excluded export remains unchanged
    failed_export.refresh_from_db()
    assert failed_export.status == 'FAILED'
    assert failed_export.re_attempt_export == False


def test_run_import_export_no_exports_when_all_failed_no_retry(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_clean_accounting_export_summary,
    setup_complete_fetching_export,
    clean_slate_exports,
    only_failed_no_retry_exports
):
    """
    Test run_import_export doesn't trigger export when all exports are failed with re_attempt_export=False
    """
    workspace_id = 1

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice', return_value=mock_export_instance)

    run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_not_called()

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)
    assert accounting_summary.last_exported_at is None

    failed_exports = AccountingExport.objects.filter(workspace_id=workspace_id, status='FAILED', re_attempt_export=False)
    assert failed_exports.count() == 2
    for export in failed_exports:
        assert export.status == 'FAILED'
        assert export.re_attempt_export == False


def test_run_import_export_include_failed_exports_with_retry_flag(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_accounting_export_summary,
    setup_complete_fetching_export,
    clean_slate_exports,
    only_failed_with_retry_exports
):
    """
    Test run_import_export includes failed exports when re_attempt_export=True
    """
    workspace_id = 1

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice', return_value=mock_export_instance)

    run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_called_once()
    call_args = mock_export_instance.trigger_export.call_args
    accounting_export_ids = call_args[1]['accounting_export_ids']

    retry_exports = AccountingExport.objects.filter(workspace_id=workspace_id, status='FAILED', re_attempt_export=True)
    expected_ids = list(retry_exports.values_list('id', flat=True))
    assert set(accounting_export_ids) == set(expected_ids)
    assert len(expected_ids) == 2
