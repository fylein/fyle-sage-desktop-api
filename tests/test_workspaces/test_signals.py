from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, ExpenseStateEnum

from apps.workspaces.models import ExportSetting


def test_run_pre_save_export_settings_triggers_reimbursable_state_change(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when reimbursable expense state changes from PAID to PAYMENT_PROCESSING
    """
    workspace_id = 1

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_async = mocker.patch('apps.workspaces.signals.async_task')

    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    existing_export_setting.save()

    mock_async.assert_called_once_with(
        'apps.fyle.tasks.import_expenses',
        workspace_id=workspace_id,
        fund_source='PERSONAL_CASH_ACCOUNT',
        fund_source_key='PERSONAL',
        imported_from=ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    )


def test_run_pre_save_export_settings_triggers_ccc_state_change(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when corporate credit card expense state changes from PAID to APPROVED
    """
    workspace_id = 2

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_async = mocker.patch('apps.workspaces.signals.async_task')

    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.APPROVED
    existing_export_setting.save()

    mock_async.assert_called_once_with(
        'apps.fyle.tasks.import_expenses',
        workspace_id=workspace_id,
        fund_source='PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT',
        fund_source_key='CCC',
        imported_from=ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    )


def test_run_pre_save_export_settings_triggers_both_state_changes(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when both reimbursable and CCC expense states change to trigger conditions
    """
    workspace_id = 3

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_async = mocker.patch('apps.workspaces.signals.async_task')

    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.APPROVED
    existing_export_setting.save()

    assert mock_async.call_count == 2

    calls = mock_async.call_args_list
    assert calls[0] == mocker.call(
        'apps.fyle.tasks.import_expenses',
        workspace_id=workspace_id,
        source_account_type='PERSONAL_CASH_ACCOUNT',
        fund_source_key='PERSONAL',
        imported_from=ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    )
    assert calls[1] == mocker.call(
        'apps.fyle.tasks.import_expenses',
        workspace_id=workspace_id,
        source_account_type='PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT',
        fund_source_key='CCC',
        imported_from=ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    )


def test_run_pre_save_export_settings_triggers_wrong_state_transition(db, mocker, create_temp_workspace, add_fyle_credentials, add_sage300_creds, add_export_settings):
    """
    Test when expense states change but not to the expected transitions
    """
    workspace_id = 1

    existing_export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAID
    existing_export_setting.save()

    mock_async = mocker.patch('apps.workspaces.signals.async_task')

    existing_export_setting.reimbursable_expense_state = ExpenseStateEnum.APPROVED
    existing_export_setting.credit_card_expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    existing_export_setting.save()

    mock_async.assert_not_called()
