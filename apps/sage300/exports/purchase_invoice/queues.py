from typing import List
from django.db.models import Q
from django_q.tasks import Chain
from django.db.models import Q
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import FyleCredential


def import_fyle_dimensions(fyle_credentials: FyleCredential):

    platform = PlatformConnector(fyle_credentials)
    platform.import_fyle_dimensions()


def check_accounting_export_and_start_import(workspace_id: int, accounting_export_ids: List[str]):
    """
    Check accounting export group and start export
    """

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    accounting_exports = AccountingExport.objects.filter(
        ~Q(status__in=['IN_PROGRESS', 'COMPLETE']),
        workspace_id=workspace_id, id__in=accounting_export_ids, purchaseinvoice__id__isnull=True,
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
                'type': 'PURCHASE_INVOICE'
            }
        )

        if accounting_export.status not in ['IN_PROGRESS', 'ENQUEUED']:
            accounting_export.status = 'ENQUEUED'
            accounting_export.save()

        """
        Todo: Add last export details
        """

        chain.append('apps.sage300.exports.purchase_invoice.tasks.create_purchase_invoice', accounting_export)

    if chain.length() > 1:
        chain.run()
