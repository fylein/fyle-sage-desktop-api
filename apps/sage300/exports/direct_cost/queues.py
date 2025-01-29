from datetime import datetime
from typing import List
import logging

from django.db.models import Q
from apps.sage300.exports.direct_cost.models import DirectCost
from django_q.models import Schedule
from django_q.tasks import Chain

from apps.accounting_exports.models import AccountingExport, Error
from apps.sage300.actions import update_accounting_export_summary
from apps.sage300.exports.helpers import resolve_errors_for_exported_accounting_export, validate_failing_export
from apps.sage300.utils import SageDesktopConnector
from apps.workspaces.models import FyleCredential, Sage300Credential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def check_accounting_export_and_start_import(workspace_id: int, accounting_export_ids: List[str], is_auto_export: bool, interval_hours: int):
    """
    Check accounting export group and start export
    """

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    accounting_exports = AccountingExport.objects.filter(
        ~Q(status__in=['IN_PROGRESS', 'COMPLETE', 'EXPORT_QUEUED']),
        workspace_id=workspace_id, id__in=accounting_export_ids, directcost__id__isnull=True,
        exported_at__isnull=True
    ).all()

    errors = Error.objects.filter(workspace_id=workspace_id, is_resolved=False, accounting_export_id__in=accounting_export_ids).all()

    chain = Chain()
    chain.append('apps.fyle.helpers.sync_dimensions', fyle_credentials)

    for index, accounting_export_group in enumerate(accounting_exports):
        error = errors.filter(workspace_id=workspace_id, accounting_export=accounting_export_group, is_resolved=False).first()
        skip_export = validate_failing_export(is_auto_export, interval_hours, error)
        if skip_export:
            logger.info('Skipping expense group %s as it has %s errors for workspace_id %s', accounting_export_group.id, error.repetition_count, workspace_id)
            continue

        accounting_export, _ = AccountingExport.objects.update_or_create(
            workspace_id=accounting_export_group.workspace_id,
            id=accounting_export_group.id,
            defaults={
                'status': 'ENQUEUED',
                'type': 'DIRECT_COST'
            }
        )

        if accounting_export.status not in ['IN_PROGRESS', 'ENQUEUED']:
            accounting_export.status = 'ENQUEUED'
            accounting_export.save()

        last_export = False
        if accounting_exports.count() == index + 1:
            last_export = True

        chain.append('apps.sage300.exports.direct_cost.tasks.create_direct_cost', accounting_export, last_export)
        chain.append('apps.sage300.exports.direct_cost.queues.create_schedule_for_polling', workspace_id, last_export)

    if chain.length() > 1:
        chain.run()


def create_schedule_for_polling(workspace_id: int, last_export: bool):
    """
    Create Schedule for running operation status polling

    Returns:
        None
    """

    Schedule.objects.update_or_create(
        func='apps.sage300.exports.direct_cost.queues.poll_operation_status',
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
    accounting_exports = AccountingExport.objects.filter(status='EXPORT_QUEUED', workspace_id=workspace_id, type='DIRECT_COST').all()

    if not accounting_exports:
        schedule = Schedule.objects.filter(args=workspace_id, func='apps.sage300.exports.direct_cost.queues.poll_operation_status').first()
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

        # Check if the operation is disabled
        if operation_status['CompletedOn']:
            # Retrieve Sage 300 errors for the current export

            document = sage300_connection.connection.documents.get(accounting_export.export_id)
            if document['CurrentState'] != '9':
                sage300_errors = sage300_connection.connection.event_failures.get(accounting_export.export_id)
                # Update the accounting export object with Sage 300 errors and status
                accounting_export.sage300_errors = sage300_errors
                accounting_export.status = 'FAILED'

                # Save the updated accounting export
                accounting_export.save()

                error, _ = Error.objects.update_or_create(
                    workspace_id=accounting_export.workspace_id,
                    accounting_export=accounting_export,
                    defaults={
                        'error_title': 'Failed to create Direct Cost',
                        'type': 'SAGE300_ERROR',
                        'error_detail': sage300_errors,
                        'is_resolved': False
                    }
                )

                error.increase_repetition_count_by_one()

                # delete direct cost from db
                direct_cost_instance = DirectCost.objects.filter(workspace_id=workspace_id, accounting_export_id=accounting_export.id)

                direct_cost_instance.delete()

        else:
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
