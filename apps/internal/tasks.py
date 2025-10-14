import logging
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from django_q.models import OrmQ, Schedule
from django_q.tasks import async_task

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import Workspace

logger = logging.getLogger(__name__)
logger.level = logging.INFO


target_func = ['apps.sage300.exports.direct_cost.tasks.create_direct_cost', 'apps.sage300.exports.purchase_invoice.tasks.create_purchase_invoice']


def re_export_stuck_exports():
    """
    Re-exports stuck accounting exports that have been in ENQUEUED or IN_PROGRESS state
    for more than 60 minutes. Skips exports that are already in the queue.
    """
    # Get production workspaces
    prod_workspace_ids = Workspace.objects.filter(
        ~Q(name__icontains='fyle for') & ~Q(name__icontains='test')
    ).values_list('id', flat=True)

    # Find stuck exports
    accounting_exports = AccountingExport.objects.filter(
        status__in=['ENQUEUED', 'IN_PROGRESS'],
        updated_at__lt=timezone.now() - timedelta(minutes=60),
        updated_at__gt=timezone.now() - timedelta(days=7),
        workspace_id__in=prod_workspace_ids
    ).select_related('workspace')

    export_count = accounting_exports.count()
    if export_count == 0:
        return

    logger.info('Found %s stuck accounting exports', export_count)

    # Get unique workspace IDs and export IDs
    workspace_ids = set(accounting_exports.values_list('workspace_id', flat=True))
    accounting_export_ids = set(accounting_exports.values_list('id', flat=True))

    # Check existing tasks in queue
    for orm in OrmQ.objects.all():
        task_data = orm.task()
        if not ('chain' in task_data and task_data['chain']):
            continue

        for chain in task_data['chain']:
            if (len(chain) > 1 and chain[0] in target_func and isinstance(chain[1][0], int)):
                logger.info('Skipping Re Export For Expense Log %s', chain[1][0])
                accounting_export_ids.remove(chain[1][0])

    logger.info('Re-exporting Accouting Export IDs: %s', accounting_export_ids)
    # Update status of exports to be re-exported
    AccountingExport.objects.filter(id__in=accounting_export_ids).update(
        status='FAILED',
        updated_at=datetime.now(timezone.utc),
        re_attempt_export=True
    )

    # Schedule re-exports for affected workspaces
    workspaces = Workspace.objects.filter(id__in=workspace_ids)
    schedules = Schedule.objects.filter(
        args__in=[str(workspace.id) for workspace in workspaces],
        func='apps.workspaces.tasks.run_import_export'
    )

    for workspace in workspaces:
        schedule = schedules.filter(args=str(workspace.id)).first()
        if not schedule or schedule.next_run >= timezone.now() + timedelta(minutes=60):
            logger.info('Scheduling re-export for workspace %s', workspace.id)
            async_task('apps.workspaces.tasks.run_import_export', workspace.id)
