from typing import List
import logging
from datetime import datetime
from django.db.models import Q
from django_q.tasks import Chain
from django_q.models import Schedule

from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.models import FyleCredential
from apps.workspaces.models import Sage300Credential
from apps.sage300.utils import SageDesktopConnector
from apps.sage300.actions import update_accounting_export_summary
from apps.sage300.exports.helpers import resolve_errors_for_exported_accounting_export
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def import_fyle_dimensions(fyle_credentials: FyleCredential):

    platform = PlatformConnector(fyle_credentials)
    platform.import_fyle_dimensions()


def check_accounting_export_and_start_import(workspace_id: int, accounting_export_ids: List[str]):
    """
    Check accounting export group and start export
    """

    # fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    accounting_exports = AccountingExport.objects.filter(
        ~Q(status__in=['IN_PROGRESS', 'COMPLETE', 'EXPORT_QUEUED']),
        workspace_id=workspace_id, id__in=accounting_export_ids, purchaseinvoice__id__isnull=True,
        exported_at__isnull=True
    ).all()

    chain = Chain()

    # Todo: uncomment this later
    # chain.append('apps.fyle.helpers.sync_dimensions', fyle_credentials)

    for index, accounting_export_group in enumerate(accounting_exports):
        accounting_export, _ = AccountingExport.objects.update_or_create(
            workspace_id=accounting_export_group.workspace_id,
            id=accounting_export_group.id,
            defaults={
                'status': 'ENQUEUED',
                'type': 'PURCHASE_INVOICE'
            }
        )

        if accounting_export.status not in ['IN_PROGRESS', 'ENQUEUED']:
            accounting_export.status = 'ENQUEUED'
            accounting_export.save()

        last_export = False
        if accounting_exports.count() == index + 1:
            last_export = True

        chain.append('apps.sage300.exports.purchase_invoice.tasks.create_purchase_invoice', accounting_export, last_export)
        chain.append('apps.sage300.exports.purchase_invoice.queues.create_schedule_for_polling', workspace_id, last_export)

    if chain.length() > 1:
        chain.run()


def create_schedule_for_polling(workspace_id: int, last_export: bool):
    """
    Create Schedule for running operation status polling

    Returns:
        None
    """

    Schedule.objects.update_or_create(
        func='apps.sage300.exports.purchase_invoice.queues.poll_operation_status',
        args='{},{}'.format(workspace_id, last_export),
        defaults={
            'schedule_type': Schedule.MINUTES,
            'minutes': 5,
            'next_run': datetime.now()
        }
    )


def poll_operation_status(workspace_id: int, last_export: bool):
    """
    Polls the operation status for queued accounting exports and updates their status accordingly.

    Args:
        workspace_id (int): The ID of the workspace.

    Returns:
        None
    """

    # Retrieve all queued accounting exports for purchase invoices
    accounting_exports = AccountingExport.objects.filter(status='EXPORT_QUEUED', workspace_id=workspace_id, type='PURCHASE_INVOICE').all()

    if not accounting_exports:
        schedule = Schedule.objects.filter(args=workspace_id, func='apps.sage300.exports.purchase_invoice.queues.poll_operation_status').first()
        if schedule:
            schedule.delete()

        return

    # Retrieve Sage 300 credentials for the workspace
    sage300_credentials = Sage300Credential.objects.filter(workspace_id=workspace_id).first()

    # Establish a connection to Sage 300 using the obtained credentials
    sage300_connection = SageDesktopConnector(sage300_credentials, workspace_id)

    # Iterate through each queued accounting export
    for accounting_export in accounting_exports:
        export_id = accounting_export.detail.get('export_id')

        # Get the operation status for the current export_id from Sage 300
        operation_status = sage300_connection.connection.operation_status.get(export_id=export_id)
        logger.info('operation status for export id %s: %s', export_id, operation_status)

        # Check if the operation is disabled
        if operation_status['CompletedOn']:
            # Retrieve Sage 300 errors for the current export
            document = sage300_connection.connection.documents.get(accounting_export.export_id)
            logger.info('expense for export id %s: %s', export_id, document)

            if str(document['CurrentState']) != '9':
                sage300_errors = sage300_connection.connection.event_failures.get(accounting_export.export_id)
                logger.info('export failed with errors: %s', sage300_errors)
                # Update the accounting export object with Sage 300 errors and status
                accounting_export.sage300_errors = sage300_errors
                accounting_export.status = 'FAILED'

                # Save the updated accounting export
                accounting_export.save()
                Error.objects.update_or_create(
                    workspace_id=accounting_export.workspace_id,
                    accounting_export=accounting_export,
                    defaults={
                        'error_title': 'Failed to create purchase invoice',
                        'type': 'SAGE300_ERROR',
                        'error_detail': sage300_errors,
                        'is_resolved': False
                    }
                )

                # Save the updated accounting export
                accounting_export.save()

                # delete purchase invoice from db
                purchase_invoice_instance = PurchaseInvoice.objects.filter(workspace_id=workspace_id, accounting_export_id=accounting_export.id)
                purchase_invoice_lineitems_instance = PurchaseInvoiceLineitems.objects.filter(workspace_id=workspace_id, purchase_invoice_id__in=purchase_invoice_instance.values_list('id', flat=True))

                purchase_invoice_lineitems_instance.delete()
                purchase_invoice_instance.delete()

                # Continue to the next iteration
                continue

        accounting_export.status = 'COMPLETE'
        accounting_export.sage300_errors = None
        detail = accounting_export.detail
        detail['operation_status'] = operation_status
        accounting_export.detail = detail
        accounting_export.exported_at = datetime.now()
        accounting_export.save()
        resolve_errors_for_exported_accounting_export(accounting_export)

        if last_export:
            update_accounting_export_summary(workspace_id=workspace_id)
