"""
All the tasks which are queued into RabbitMQ
    * User Triggered Async Tasks
    * Schedule Triggered Async Tasks
"""
import logging

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, WebhookAttributeActionEnum

from apps.accounting_exports.models import AccountingExport
from apps.fyle.helpers import assert_valid_request
from apps.fyle.tasks import import_credit_card_expenses, import_reimbursable_expenses
from apps.workspaces.models import FeatureConfig
from fyle_integrations_imports.modules.webhook_attributes import WebhookAttributeProcessor
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq

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
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.IMPORT_REIMBURSABLE_EXPENSES.value,
            'data': {
                'workspace_id': workspace_id,
                'accounting_export': accounting_export.id,
                'imported_from': imported_from
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)
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
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.IMPORT_CREDIT_CARD_EXPENSES.value,
            'data': {
                'workspace_id': workspace_id,
                'accounting_export': accounting_export.id,
                'imported_from': imported_from
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)
        return

    import_credit_card_expenses(workspace_id, accounting_export, imported_from)


def async_handle_webhook_callback(body: dict, workspace_id: int) -> None:
    """
    Async'ly import and export expenses
    :param body: body
    :return: None
    """
    logger.info('Received webhook callback for workspace_id: {}, payload: {}'.format(workspace_id, body))
    action = body.get('action')
    resource = body.get('resource')
    data = body.get('data')
    org_id = data.get('org_id') if data else None
    assert_valid_request(workspace_id=workspace_id, org_id=org_id)

    if action in ('ADMIN_APPROVED', 'APPROVED', 'STATE_CHANGE_PAYMENT_PROCESSING', 'PAID') and data:
        report_id = data['id']
        state = data['state']

        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.EXPENSE_STATE_CHANGE.value,
            'data': {
                'workspace_id': workspace_id,
                'report_id': report_id,
                'is_state_change_event': True,
                'report_state': state,
                'imported_from': ExpenseImportSourceEnum.WEBHOOK,
                'trigger_export': True,
                'triggered_by': ExpenseImportSourceEnum.WEBHOOK
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.EXPORT_P1.value)

    elif action == 'ACCOUNTING_EXPORT_INITIATED' and data:
        # No direct export for Sage 300
        pass

    elif body.get('action') == 'UPDATED_AFTER_APPROVAL' and body.get('data') and resource == 'EXPENSE':
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.EXPENSE_UPDATED_AFTER_APPROVAL.value,
            'data': {
                'data': body['data']
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.UTILITY.value)

    elif body.get('action') in ('EJECTED_FROM_REPORT', 'ADDED_TO_REPORT') and body.get('data') and resource == 'EXPENSE':
        expense_id = body['data']['id']
        action = body.get('action')
        logger.info("| Handling expense %s | Content: {WORKSPACE_ID: %s EXPENSE_ID: %s Payload: %s}", action.lower().replace('_', ' '), workspace_id, expense_id, body.get('data'))
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.EXPENSE_ADDED_EJECTED_FROM_REPORT.value,
            'data': {
                'expense_data': body['data'],
                'action_type': action
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.UTILITY.value)

    elif action == 'UPDATED' and resource == 'ORG_SETTING':
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.HANDLE_ORG_SETTING_UPDATED.value,
            'data': {
                'workspace_id': workspace_id,
                'org_settings': data
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.UTILITY.value)

    elif action in (WebhookAttributeActionEnum.CREATED, WebhookAttributeActionEnum.UPDATED, WebhookAttributeActionEnum.DELETED):
        try:
            fyle_webhook_sync_enabled = FeatureConfig.get_feature_config(workspace_id=workspace_id, key='fyle_webhook_sync_enabled')
            if fyle_webhook_sync_enabled:
                logger.info("| Processing attribute webhook | Content: {{WORKSPACE_ID: {} Payload: {}}}".format(workspace_id, body))
                processor = WebhookAttributeProcessor(workspace_id)
                processor.process_webhook(body)
        except Exception as e:
            logger.error(f"Error processing attribute webhook for workspace {workspace_id}: {str(e)}")
