from typing import List
from datetime import datetime, timedelta
from django.db.models import Q
from django_q.tasks import Chain
from django_q.models import Schedule

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import FyleCredential
from apps.workspaces.models import Sage300Credential
from apps.sage300.utils import SageDesktopConnector


def check_accounting_export_and_start_import(workspace_id: int, accounting_export_ids: List[str]):
    """
    Check accounting export group and start export
    """

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    accounting_exports = AccountingExport.objects.filter(
        ~Q(status__in=['IN_PROGRESS', 'COMPLETE', 'EXPORT_QUEUED']),
        workspace_id=workspace_id, id__in=accounting_export_ids, directcost__id__isnull=True,
        exported_at__isnull=True
    ).all()

    chain = Chain()
    chain.append('apps.fyle.helpers.sync_dimensions', fyle_credentials)

    for index, accounting_export_group in enumerate(accounting_exports):
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

        """
        Todo: Add last export details
        """

        chain.append('apps.sage300.exports.direct_cost.tasks.create_direct_cost', accounting_export)

    if chain.length() > 1:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.sage300.exports.direct_cost.queues.poll_operation_status',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 5,
                'next_run': datetime.now() + timedelta(minutes=10)
            }
        )
        chain.run()


def poll_operation_status(workspace_id: int):
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
        if operation_status.get('DisabledOn'):

            # Retrieve Sage 300 errors for the current export
            sage300_errors = sage300_connection.connection.events_failure.get(accounting_export.export_id)

            # Update the accounting export object with Sage 300 errors and status
            accounting_export.sage300_errors = sage300_errors
            accounting_export.status = 'FAILED'

            # Save the updated accounting export
            accounting_export.save()

            # Continue to the next iteration
            continue

        accounting_export.status = 'COMPLETE'
        detail = accounting_export.detail
        detail['operation_status'] = operation_status
        accounting_export.detail = detail
        accounting_export.exported_at = datetime.now()
        accounting_export.save()
