from apps.fyle.exceptions import handle_exceptions
from fyle.platform.exceptions import (
    NoPrivilegeError,
    RetryException
)
from apps.workspaces.models import FyleCredential
from apps.accounting_exports.models import AccountingExport


def test_handle_exceptions(
    db,
    mocker,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses,
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    @handle_exceptions
    def test_func(workspace_id, accounting_export):
        raise FyleCredential.DoesNotExist('Fyle credentials not found')

    test_func(1, accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == {'message': 'Fyle credentials do not exist in workspace'}

    @handle_exceptions
    def test_func(workspace_id, accounting_export):
        raise NoPrivilegeError('No privilege to access the resource')

    test_func(1, accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == {'message': 'Invalid Fyle Credentials / Admin is disabled'}

    @handle_exceptions
    def test_func(workspace_id, accounting_export):
        raise RetryException('Retry Exception')

    test_func(1, accounting_export)

    assert accounting_export.status == 'FATAL'
    assert accounting_export.detail == {'message': 'Fyle Retry Exception occured'}

    @handle_exceptions
    def test_func(workspace_id, accounting_export):
        raise Exception('Random Exception')

    test_func(1, accounting_export)

    assert accounting_export.status == 'FATAL'
