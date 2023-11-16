from typing import List
from django_q.tasks import Chain

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import FyleCredential


def check_accounting_export_and_start_import(self, export_type: str, accounting_exports: List[AccountingExport]):
    """
    Check accounting export group and start export
    """

    fyle_credentials = FyleCredential.objects.filter(workspace_id=self.workspace_id)

    chain = Chain()
    chain.append('apps.fyle.helpers.sync_dimensions', fyle_credentials, self.workspace_id)
    for index, accounting_export_group in enumerate(accounting_exports):
        accounting_export, _ = AccountingExport.objects.get_or_create(
            workspace_id=accounting_export_group.workspace_id,
            id=accounting_export_group.id,
            defaults={
                'status': 'ENQUEUED',
                'type': export_type
            }
        )
        if accounting_export.status not in ['IN_PROGRESS', 'ENQUEUED']:
            accounting_export.status = 'ENQUEUED'
            accounting_export.save()

        last_export = False
        if accounting_export.count() == index + 1:
            last_export = True

            chain.append('apps.sage300.purchase_invoice.queues.create_purchase_invoice', accounting_export, last_export)

        if chain.length() > 1:
            chain.run()
