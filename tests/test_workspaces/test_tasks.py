from datetime import datetime, timedelta

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.urls import reverse
from django_q.models import Schedule
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.workspaces.models import AdvancedSetting, ExportSetting, FyleCredential
from apps.workspaces.signals import run_post_save_export_settings_triggers, run_pre_save_export_settings_triggers
from apps.workspaces.models import Workspace
from apps.workspaces.tasks import (
    async_create_admin_subscriptions,
    async_update_fyle_credentials,
    export_to_sage300,
    run_import_export,
    trigger_run_import_export,
    schedule_sync,
    sync_org_settings,
)
from workers.helpers import WorkerActionEnum, RoutingKeyEnum


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


def test_run_import_export_publishes_to_rabbitmq(
    db,
    mocker,
    create_temp_workspace
):
    """Test that run_import_export publishes the correct payload to RabbitMQ"""
    workspace_id = 1
    mock_publish = mocker.patch('apps.workspaces.tasks.publish_to_rabbitmq')

    run_import_export(workspace_id=workspace_id)

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args[1]
    assert call_kwargs['payload']['workspace_id'] == workspace_id
    assert call_kwargs['payload']['action'] == WorkerActionEnum.RUN_SYNC_SCHEDULE.value
    assert call_kwargs['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


def test_trigger_run_import_export_with_reimbursable_expense(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_feature_config
):
    workspace_id = 1
    accounting_summary, created = AccountingExportSummary.objects.get_or_create(
        workspace_id=workspace_id,
        defaults={'export_mode': 'MANUAL'}
    )
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

    trigger_run_import_export(workspace_id=workspace_id)

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


def test_trigger_run_import_export_with_credit_card_expense(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_feature_config
):
    workspace_id = 1
    accounting_summary, created = AccountingExportSummary.objects.get_or_create(
        workspace_id=workspace_id,
        defaults={'export_mode': 'MANUAL'}
    )
    # Get the specific FETCHING export and set it up
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

    trigger_run_import_export(workspace_id=workspace_id)

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
    add_accounting_export_expenses,
    add_feature_config
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


def test_export_to_sage300_with_ccc(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_expenses,
    add_feature_config
):
    """Test export_to_sage300 with credit card expense export type set"""
    workspace_id = 1
    AccountingExportSummary.objects.create(workspace_id=workspace_id)

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = None
    export_settings.credit_card_expense_export_type = 'DIRECT_COST'
    export_settings.save()

    # Set up CCC accounting export as unexported
    ccc_export = AccountingExport.objects.filter(
        workspace_id=workspace_id, fund_source='CCC'
    ).first()
    ccc_export.status = 'EXPORT_READY'
    ccc_export.exported_at = None
    ccc_export.save()

    # Patch at the import location in workspaces.tasks
    mock_export_direct_cost = mocker.patch('apps.workspaces.tasks.ExportDirectCost')
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice')

    export_to_sage300(workspace_id=workspace_id, triggered_by=ExpenseImportSourceEnum.DIRECT_EXPORT)

    mock_export_direct_cost.return_value.trigger_export.assert_called_once()
    call_kwargs = mock_export_direct_cost.return_value.trigger_export.call_args[1]
    assert call_kwargs['run_in_rabbitmq_worker'] is True

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)
    assert accounting_summary.last_exported_at is not None


def test_async_create_admin_subscriptions(
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
    async_create_admin_subscriptions(workspace_id=workspace_id)

    expected_payload = {
        'data': {
            'is_enabled': True,
            'webhook_url': '{}/workspaces/{}/fyle/webhook_callback/'.format(settings.API_URL, workspace_id),
            'subscribed_resources': [
                'EXPENSE',
                'REPORT',
                'CATEGORY',
                'PROJECT',
                'COST_CENTER',
                'EXPENSE_FIELD',
                'CORPORATE_CARD',
                'EMPLOYEE',
                'ORG_SETTING'
            ]
        }
    }

    mock_api.assert_called_once_with(expected_payload)

    mock_api.side_effect = Exception('Error')
    try:
        async_create_admin_subscriptions(workspace_id=workspace_id)
    except Exception as e:
        assert str(e) == 'Error'


def test_async_create_admin_subscriptions_2(
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


def test_trigger_run_import_export_exclude_failed_exports_reimbursable(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_summary,
    add_basic_retry_exports,
    add_feature_config
):
    """
    Test trigger_run_import_export excludes failed reimbursable exports with re_attempt_export=False
    """
    workspace_id = 1

    AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES',
        defaults={'status': 'COMPLETE'}
    )

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice', return_value=mock_export_instance)

    trigger_run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_called_once()
    call_args = mock_export_instance.trigger_export.call_args
    accounting_export_ids = call_args[1]['accounting_export_ids']

    ready_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='EXPORT_READY', type='PURCHASE_INVOICE')
    retry_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='FAILED', re_attempt_export=True, type='PURCHASE_INVOICE')
    failed_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='FAILED', re_attempt_export=False, type='PURCHASE_INVOICE')

    expected_ids = [ready_export.id, retry_export.id]
    assert set(accounting_export_ids) == set(expected_ids)
    assert failed_export.id not in accounting_export_ids

    failed_export.refresh_from_db()
    assert failed_export.status == 'FAILED'
    assert failed_export.re_attempt_export == False


def test_trigger_run_import_export_exclude_failed_exports_credit_card(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_summary,
    add_basic_credit_card_exports,
    add_feature_config
):
    """
    Test trigger_run_import_export excludes failed credit card exports with re_attempt_export=False
    """
    workspace_id = 1

    AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_CREDIT_CARD_EXPENSES',
        defaults={'status': 'COMPLETE'}
    )

    post_save.disconnect(run_post_save_export_settings_triggers, sender=ExportSetting)
    pre_save.disconnect(run_pre_save_export_settings_triggers, sender=ExportSetting)

    try:
        export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
        export_settings.reimbursable_expenses_export_type = None
        export_settings.credit_card_expense_export_type = 'DIRECT_COST'
        export_settings.save()
    finally:
        # Reconnect signals
        post_save.connect(run_post_save_export_settings_triggers, sender=ExportSetting)
        pre_save.connect(run_pre_save_export_settings_triggers, sender=ExportSetting)

    mocker.patch('apps.workspaces.tasks.queue_import_credit_card_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportDirectCost', return_value=mock_export_instance)

    trigger_run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_called_once()
    call_args = mock_export_instance.trigger_export.call_args
    accounting_export_ids = call_args[1]['accounting_export_ids']

    ready_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='CCC', status='EXPORT_READY', type='DIRECT_COST')
    retry_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='CCC', status='FAILED', re_attempt_export=True, type='DIRECT_COST')
    failed_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='CCC', status='FAILED', re_attempt_export=False, type='DIRECT_COST')

    expected_ids = [ready_export.id, retry_export.id]
    assert set(accounting_export_ids) == set(expected_ids)
    assert failed_export.id not in accounting_export_ids

    # Verify excluded export remains unchanged
    failed_export.refresh_from_db()
    assert failed_export.status == 'FAILED'
    assert failed_export.re_attempt_export == False


def test_trigger_run_import_export_no_exports_when_all_failed_no_retry(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_summary,
    add_basic_retry_exports,
    add_feature_config
):
    """
    Test trigger_run_import_export doesn't trigger export when all exports are failed with re_attempt_export=False
    """
    workspace_id = 1

    summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)
    summary.last_exported_at = None
    summary.save()

    AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES',
        defaults={'status': 'COMPLETE'}
    )

    AccountingExport.objects.filter(
        workspace_id=workspace_id,
        fund_source='PERSONAL',
        type='PURCHASE_INVOICE'
    ).exclude(status='FAILED', re_attempt_export=False).delete()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice', return_value=mock_export_instance)

    trigger_run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_not_called()

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)
    assert accounting_summary.last_exported_at is None

    failed_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='FAILED', re_attempt_export=False, type='PURCHASE_INVOICE')
    assert failed_export.status == 'FAILED'
    assert failed_export.re_attempt_export == False


def test_trigger_run_import_export_include_failed_exports_with_retry_flag(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_export_settings,
    add_advanced_settings,
    add_accounting_export_summary,
    add_basic_retry_exports,
    add_feature_config
):
    """
    Test trigger_run_import_export includes failed exports when re_attempt_export=True
    """
    workspace_id = 1

    AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES',
        defaults={'status': 'COMPLETE'}
    )

    AccountingExport.objects.filter(
        workspace_id=workspace_id,
        fund_source='PERSONAL',
        type='PURCHASE_INVOICE'
    ).exclude(status='FAILED', re_attempt_export=True).delete()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_instance = mocker.Mock()
    mocker.patch('apps.workspaces.tasks.ExportPurchaseInvoice', return_value=mock_export_instance)

    trigger_run_import_export(workspace_id=workspace_id)

    mock_export_instance.trigger_export.assert_called_once()
    call_args = mock_export_instance.trigger_export.call_args
    accounting_export_ids = call_args[1]['accounting_export_ids']

    retry_export = AccountingExport.objects.get(workspace_id=workspace_id, fund_source='PERSONAL', status='FAILED', re_attempt_export=True, type='PURCHASE_INVOICE')
    expected_ids = [retry_export.id]
    assert set(accounting_export_ids) == set(expected_ids)


def test_sync_org_settings(db, mocker, create_temp_workspace, add_fyle_credentials):
    """
    Test sync org settings
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.org_settings = {}
    workspace.save()

    mock_platform = mocker.patch('apps.workspaces.tasks.PlatformConnector')
    mock_platform.return_value.org_settings.get.return_value = {
        'regional_settings': {
            'locale': {
                'date_format': 'DD/MM/YYYY',
                'timezone': 'Asia/Kolkata'
            }
        }
    }

    sync_org_settings(workspace_id=workspace_id)

    workspace.refresh_from_db()
    assert workspace.org_settings == {
        'regional_settings': {
            'locale': {
                'date_format': 'DD/MM/YYYY',
                'timezone': 'Asia/Kolkata'
            }
        }
    }
