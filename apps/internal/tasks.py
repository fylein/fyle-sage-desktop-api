import logging
from datetime import datetime, timedelta

from django.db.models import Q
from django_q.models import OrmQ

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import Workspace

# from django_q.tasks import async_task


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def re_export_stuck_exports():
    prod_workspace_ids = Workspace.objects.filter(
        ~Q(name__icontains='fyle for') & ~Q(name__icontains='test')
    ).values_list('id', flat=True)
    accounting_exports = AccountingExport.objects.filter(
        status__in=['ENQUEUED', 'IN_PROGRESS'],
        updated_at__lt=datetime.now() - timedelta(minutes=60),
        workspace_id__in=prod_workspace_ids
    )
    if accounting_exports.count() > 0:
        logger.info('Re-exporting stuck accounting_exports')
        logger.info('%s stuck task_logs found', accounting_exports.count())
        # workspace_ids = accounting_exports.values_list('workspace_id', flat=True).distinct()
        accounting_export_ids = accounting_exports.values_list('id', flat=True)
        ormqs = OrmQ.objects.all()
        for orm in ormqs:
            if 'chain' in orm.task and orm.task['chain']:
                for chain in orm.task['chain']:
                    if len(chain) > 1 and isinstance(chain[1], list) and isinstance(chain[1][0], AccountingExport):
                        if chain[1][0].id in accounting_export_ids:
                            logger.info('Skipping Re Export For Expense Log %s', chain[1][0].id)
                            accounting_export_ids.remove(chain[1][0].id)

        logger.info('Re-exporting Accouting Export IDs: %s', accounting_export_ids)
        # reexport_accounting_exports = accounting_exports.filter(id__in=accounting_export_ids)
        # expenses = []
        # for reexport_accounting_export in reexport_accounting_exports:
        #     expenses.extend(reexport_accounting_export.expenses.all())
        # workspace_ids_list = list(workspace_ids)
        # reexport_accounting_export.update(status='FAILED', updated_at=datetime.now())
        # workspaces = Workspace.objects.filter(id__in=workspace_ids_list)
        # schedules = Schedule.objects.filter(
        #     args__in=[str(workspace.id) for workspace in workspaces],
        #     func='apps.workspaces.tasks.run_import_export'
        # )
        # for workspace in workspaces:
        #     logger.info('Checking if 1hour sync schedule for workspace %s', workspace.id)
        #     schedule = schedules.filter(args=str(workspace.id)).first()
        #     # If schedule exist and it's within 1 hour, need not trigger it immediately
        #     if not (schedule and schedule.next_run < datetime.now(tz=schedule.next_run.tzinfo) + timedelta(minutes=60)):
        #         logger.info('Re-triggering sync schedule since no 1 hour schedule for workspace  %s', workspace.id)
        #         async_task('apps.workspaces.tasks.run_import_export', workspace.id)
