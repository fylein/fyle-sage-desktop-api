from sage_desktop_sdk.exceptions.hh2_exceptions import WrongParamsError

from apps.sage300.exceptions import (
    handle_sage300_exceptions,
    handle_sage300_error
)
from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.models import Sage300Credential, FyleCredential
from sage_desktop_api.exceptions import BulkError


def test_handle_sage300_error(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses,
):
    workspace_id = 1
    export_type = 'Purchase Invoice'
    exception = WrongParamsError(response = 'Error', msg = 'Error')

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    handle_sage300_error(exception, accounting_export, export_type)

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).first()
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == None

    assert error.error_title == 'Failed to create Purchase Invoice'
    assert error.type == 'SAGE300_ERROR'
    assert error.error_detail == 'Error'
    assert error.is_resolved == False


def test_handle_sage300_exceptions(
    db,
    mocker,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses,
    add_accounting_export_summary,
    add_sage300_creds

):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    @handle_sage300_exceptions()
    def test_func(accounting_export):
        raise FyleCredential.DoesNotExist('Fyle credentials not found')

    test_func(accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == {'message': 'Fyle credentials do not exist in workspace'}

    @handle_sage300_exceptions()
    def test_func(accounting_export):
        raise Sage300Credential.DoesNotExist('Sage300 Account not connected / token expired')

    test_func(accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == {'accounting_export_id': accounting_export.id, 'message': 'Sage300 Account not connected / token expired'}

    @handle_sage300_exceptions()
    def test_func(accounting_export):
        raise WrongParamsError(response = 'Error', msg = 'Error')

    test_func(accounting_export)

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).first()
    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == None
    assert error.type == 'SAGE300_ERROR'
    assert error.is_resolved == False

    @handle_sage300_exceptions()
    def test_func(accounting_export):
        raise BulkError(response = 'Error', msg = 'Error')

    test_func(accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == 'Error'

    @handle_sage300_exceptions()
    def test_func(accounting_export):
        raise Exception('Error')

    test_func(accounting_export)

    assert accounting_export.status == 'FATAL'
