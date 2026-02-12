from enum import Enum

from fyle_accounting_library.rabbitmq.connector import RabbitMQConnection
from fyle_accounting_library.rabbitmq.data_class import RabbitMQData
from fyle_accounting_library.rabbitmq.enums import RabbitMQExchangeEnum


class RoutingKeyEnum(str, Enum):
    """
    Routing key enum
    """
    IMPORT = 'IMPORT.*'
    UTILITY = 'UTILITY.*'
    EXPORT_P0 = 'EXPORT.P0.*'
    EXPORT_P1 = 'EXPORT.P1.*'


class WorkerActionEnum(str, Enum):
    """
    Worker action enum
    """
    DASHBOARD_SYNC = 'EXPORT.P0.DASHBOARD_SYNC'
    DISABLE_ITEMS = 'IMPORT.DISABLE_ITEMS'
    EXPENSE_STATE_CHANGE = 'EXPORT.P1.EXPENSE_STATE_CHANGE'
    SYNC_SAGE_DIMENSION = 'IMPORT.SYNC_SAGE_DIMENSION'
    IMPORT_DIMENSIONS_TO_FYLE = 'IMPORT.IMPORT_DIMENSIONS_TO_FYLE'
    CREATE_ADMIN_SUBSCRIPTION = 'UTILITY.CREATE_ADMIN_SUBSCRIPTION'
    BACKGROUND_SCHEDULE_EXPORT = 'EXPORT.P1.BACKGROUND_SCHEDULE_EXPORT'
    RUN_SYNC_SCHEDULE = 'EXPORT.P1.RUN_SYNC_SCHEDULE'
    POLL_PURCHASE_INVOICE_STATUS = 'EXPORT.P1.POLL_PURCHASE_INVOICE_STATUS'
    POLL_DIRECT_COST_STATUS = 'EXPORT.P1.POLL_DIRECT_COST_STATUS'
    HANDLE_FYLE_REFRESH_DIMENSION = 'IMPORT.HANDLE_FYLE_REFRESH_DIMENSION'
    HANDLE_SAGE_REFRESH_DIMENSION = 'IMPORT.HANDLE_SAGE_REFRESH_DIMENSION'
    EXPENSE_UPDATED_AFTER_APPROVAL = 'UTILITY.EXPENSE_UPDATED_AFTER_APPROVAL'
    EXPENSE_ADDED_EJECTED_FROM_REPORT = 'UTILITY.EXPENSE_ADDED_EJECTED_FROM_REPORT'
    HANDLE_ORG_SETTING_UPDATED = 'UTILITY.HANDLE_ORG_SETTING_UPDATED'
    CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION = 'IMPORT.CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION'
    IMPORT_REIMBURSABLE_EXPENSES = 'IMPORT.IMPORT_REIMBURSABLE_EXPENSES'
    IMPORT_CREDIT_CARD_EXPENSES = 'IMPORT.IMPORT_CREDIT_CARD_EXPENSES'


QUEUE_BINDKEY_MAP = {
    'sage_desktop_import': RoutingKeyEnum.IMPORT,
    'sage_desktop_utility': RoutingKeyEnum.UTILITY,
    'sage_desktop_export.p0': RoutingKeyEnum.EXPORT_P0,
    'sage_desktop_export.p1': RoutingKeyEnum.EXPORT_P1
}


ACTION_METHOD_MAP = {
    WorkerActionEnum.DASHBOARD_SYNC: 'apps.workspaces.tasks.export_to_sage300',
    WorkerActionEnum.DISABLE_ITEMS: 'fyle_integrations_imports.tasks.disable_items',
    WorkerActionEnum.EXPENSE_STATE_CHANGE: 'apps.fyle.tasks.import_expenses',
    WorkerActionEnum.CREATE_ADMIN_SUBSCRIPTION: 'apps.workspaces.tasks.async_create_admin_subscriptions',
    WorkerActionEnum.BACKGROUND_SCHEDULE_EXPORT: 'apps.workspaces.tasks.export_to_sage300',
    WorkerActionEnum.RUN_SYNC_SCHEDULE: 'apps.workspaces.tasks.trigger_run_import_export',
    WorkerActionEnum.POLL_PURCHASE_INVOICE_STATUS: 'apps.sage300.exports.purchase_invoice.queues.trigger_poll_operation_status',
    WorkerActionEnum.POLL_DIRECT_COST_STATUS: 'apps.sage300.exports.direct_cost.queues.trigger_poll_operation_status',
    WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE: 'apps.mappings.queue.initiate_import_to_fyle',
    WorkerActionEnum.EXPENSE_UPDATED_AFTER_APPROVAL: 'apps.fyle.tasks.update_non_exported_expenses',
    WorkerActionEnum.EXPENSE_ADDED_EJECTED_FROM_REPORT: 'apps.fyle.tasks.handle_expense_report_change',
    WorkerActionEnum.CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION: 'apps.fyle.helpers.check_interval_and_sync_dimension',
    WorkerActionEnum.HANDLE_ORG_SETTING_UPDATED: 'apps.fyle.tasks.handle_org_setting_updated',
    WorkerActionEnum.IMPORT_REIMBURSABLE_EXPENSES: 'apps.fyle.tasks.import_reimbursable_expenses',
    WorkerActionEnum.IMPORT_CREDIT_CARD_EXPENSES: 'apps.fyle.tasks.import_credit_card_expenses',
}


def get_routing_key(queue_name: str) -> str:
    """
    Get the routing key for a given queue name
    :param queue_name: str
    :return: str
    :raises ValueError: if queue_name is not found in QUEUE_BINDKEY_MAP
    """
    routing_key = QUEUE_BINDKEY_MAP.get(queue_name)
    if routing_key is None:
        raise ValueError(f'Unknown queue name: {queue_name}. Valid queue names are: {list(QUEUE_BINDKEY_MAP.keys())}')
    return routing_key


def publish_to_rabbitmq(payload: dict, routing_key: RoutingKeyEnum) -> None:
    """
    Publish messages to RabbitMQ
    :param: payload: dict
    :param: routing_key: RoutingKeyEnum
    :return: None
    """
    rabbitmq = RabbitMQConnection.get_instance(RabbitMQExchangeEnum.SAGE_DESKTOP_EXCHANGE)
    data = RabbitMQData(new=payload)
    rabbitmq.publish(routing_key, data)
