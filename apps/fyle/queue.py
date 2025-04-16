"""
All the tasks which are queued into django-q
    * User Triggered Async Tasks
    * Schedule Triggered Async Tasks
"""
import logging
from django_q.tasks import async_task

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, RoutingKeyEnum
from fyle_accounting_library.rabbitmq.connector import RabbitMQConnection
from fyle_accounting_library.rabbitmq.data_class import RabbitMQData

from apps.fyle.tasks import (
    import_credit_card_expenses,
    import_reimbursable_expenses
)
from apps.accounting_exports.models import AccountingExport
from apps.fyle.helpers import assert_valid_request

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def queue_import_reimbursable_expenses(workspace_id: int, synchronous: bool = False, imported_from: ExpenseImportSourceEnum = None):
    """
    Queue Import of Reimbursable Expenses from Fyle
    :param workspace_id: Workspace id
    :return: None
    """
    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    if not synchronous:
        async_task(
            'apps.fyle.tasks.import_reimbursable_expenses',
            workspace_id, accounting_export, imported_from
        )
        return

    import_reimbursable_expenses(workspace_id, accounting_export, imported_from)


def queue_import_credit_card_expenses(workspace_id: int, synchronous: bool = False, imported_from: ExpenseImportSourceEnum = None):
    """
    Queue Import of Credit Card Expenses from Fyle
    :param workspace_id: Workspace id
    :return: None
    """
    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_CREDIT_CARD_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    if not synchronous:
        async_task(
            'apps.fyle.tasks.import_credit_card_expenses',
            workspace_id, accounting_export, imported_from
        )
        return

    import_credit_card_expenses(workspace_id, accounting_export, imported_from)


def async_handle_webhook_callback(body: dict, workspace_id: int) -> None:
    """
    Async'ly import and export expenses
    :param body: body
    :return: None
    """
    logger.info('Received webhook callback for workspace_id: {}, payload: {}'.format(workspace_id, body))
    rabbitmq = RabbitMQConnection.get_instance('sage_desktop_exchange')
    if body.get('action') in ('ADMIN_APPROVED', 'APPROVED', 'STATE_CHANGE_PAYMENT_PROCESSING', 'PAID') and body.get('data'):
        report_id = body['data']['id']
        org_id = body['data']['org_id']
        state = body['data']['state']
        assert_valid_request(workspace_id=workspace_id, org_id=org_id)

        payload = {
            'data': {
                'workspace_id': workspace_id,
                'report_id': report_id,
                'is_state_change_event': True,
                'report_state': state,
                'imported_from': ExpenseImportSourceEnum.WEBHOOK,
            },
            'workspace_id': workspace_id
        }
        data = RabbitMQData(
            new=payload
        )
        rabbitmq.publish(RoutingKeyEnum.EXPORT, data)

    elif body.get('action') == 'ACCOUNTING_EXPORT_INITIATED' and body.get('data'):
        # No direct export for Sage 300
        pass

    elif body.get('action') == 'UPDATED_AFTER_APPROVAL' and body.get('data') and body.get('resource') == 'EXPENSE':
        org_id = body['data']['org_id']
        assert_valid_request(workspace_id=workspace_id, org_id=org_id)
        async_task('apps.fyle.tasks.update_non_exported_expenses', body['data'])
