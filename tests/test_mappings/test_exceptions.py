from apps.mappings.exceptions import (
    handle_import_exceptions_v2
)
from sage_desktop_sdk.exceptions import InvalidUserCredentials
from fyle_integrations_imports.models import ImportLog
from fyle.platform.exceptions import (
    WrongParamsError,
    RetryException,
    InternalServerError,
    InvalidTokenError as FyleInvalidTokenError
)


def test_handle_import_exceptions_v2(
    db,
    create_temp_workspace,
    create_expense_attribute
):
    workspace_id = 1
    expense_attribute = create_expense_attribute
    import_log = ImportLog.objects.create(
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE',
        status='IN_PROGRESS'
    )

    @handle_import_exceptions_v2
    def test_func(expense_attribute_instance, import_log):
        raise WrongParamsError('Wrong Params Error')

    test_func(expense_attribute, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['message'] == 'Wrong Params Error'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    @handle_import_exceptions_v2
    def test_func(expense_attribute_instance, import_log):
        raise InvalidUserCredentials('Invalid Token')

    test_func(expense_attribute, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['message'] == 'Invalid Token or Sage 300 credentials does not exist workspace_id - 1'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    @handle_import_exceptions_v2
    def test_func(expense_attribute_instance, import_log):
        raise RetryException('Retry Exception')

    test_func(expense_attribute, import_log)

    assert import_log.status == 'FATAL'
    assert import_log.error_log['message'] == 'Fyle Retry Exception occured'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    @handle_import_exceptions_v2
    def test_func(expense_attribute_instance, import_log):
        raise InternalServerError('Internal Server Error')

    test_func(expense_attribute, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['message'] == 'Internal server error while importing to Fyle'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    @handle_import_exceptions_v2
    def test_func(expense_attribute_instance, import_log):
        raise Exception('Exception')

    test_func(expense_attribute, import_log)

    assert import_log.status == 'FATAL'
    assert import_log.error_log['message'] == 'Something went wrong'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    @handle_import_exceptions_v2
    def test_func(expense_attribute_instance, import_log):
        raise FyleInvalidTokenError('Invalid Token for fyle')

    test_func(expense_attribute, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['message'] == 'Invalid Token for fyle'
