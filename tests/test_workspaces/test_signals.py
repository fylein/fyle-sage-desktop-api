from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, ExpenseStateEnum

from apps.workspaces.models import ExportSetting
from workers.helpers import WorkerActionEnum, RoutingKeyEnum


def test_run_pre_save_export_settings_triggers_reimbursable_state_change(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when reimbursable expense state changes from PAID to PAYMENT_PROCESSING
    """
    workspace_id = 1

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_publish = mocker.patch('apps.workspaces.signals.publish_to_rabbitmq')

    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    existing_export_setting.save()

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args[1]
    assert call_kwargs['payload']['workspace_id'] == workspace_id
    assert call_kwargs['payload']['action'] == WorkerActionEnum.EXPENSE_STATE_CHANGE.value
    assert call_kwargs['payload']['data']['source_account_type'] == 'PERSONAL_CASH_ACCOUNT'
    assert call_kwargs['payload']['data']['fund_source_key'] == 'PERSONAL'
    assert call_kwargs['payload']['data']['imported_from'] == ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    assert call_kwargs['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


def test_run_pre_save_export_settings_triggers_ccc_state_change(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when corporate credit card expense state changes from PAID to APPROVED
    """
    workspace_id = 2

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_publish = mocker.patch('apps.workspaces.signals.publish_to_rabbitmq')

    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.APPROVED
    existing_export_setting.save()

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args[1]
    assert call_kwargs['payload']['workspace_id'] == workspace_id
    assert call_kwargs['payload']['action'] == WorkerActionEnum.EXPENSE_STATE_CHANGE.value
    assert call_kwargs['payload']['data']['source_account_type'] == 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
    assert call_kwargs['payload']['data']['fund_source_key'] == 'CCC'
    assert call_kwargs['payload']['data']['imported_from'] == ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    assert call_kwargs['routing_key'] == RoutingKeyEnum.EXPORT_P1.value


def test_run_pre_save_export_settings_triggers_both_state_changes(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when both reimbursable and CCC expense states change to trigger conditions
    """
    workspace_id = 3

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_publish = mocker.patch('apps.workspaces.signals.publish_to_rabbitmq')

    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.APPROVED
    existing_export_setting.save()

    assert mock_publish.call_count == 2

    calls = mock_publish.call_args_list
    assert calls[0][1]['payload']['data']['source_account_type'] == 'PERSONAL_CASH_ACCOUNT'
    assert calls[0][1]['payload']['data']['fund_source_key'] == 'PERSONAL'
    assert calls[1][1]['payload']['data']['source_account_type'] == 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
    assert calls[1][1]['payload']['data']['fund_source_key'] == 'CCC'


def test_run_pre_save_export_settings_triggers_wrong_state_transition(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when expense states change but not to the expected transitions
    """
    workspace_id = 1

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_publish = mocker.patch('apps.workspaces.signals.publish_to_rabbitmq')

    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.APPROVED
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    existing_export_setting.save()

    mock_publish.assert_not_called()
