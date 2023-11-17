from typing import List
from django_q.tasks import Chain
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import FyleCredential
from apps.sage300.exports.purchase_invoice.tasks import ExportPurchaseInvoice


def import_fyle_dimensions(fyle_credentials: FyleCredential):

    platform = PlatformConnector(fyle_credentials)
    platform.import_fyle_dimensions()


def create_purchase_invoice(workspace_id, accounting_export):

    purchase_invoice = ExportPurchaseInvoice()
    created_purchase_invoice = purchase_invoice.create_purchase_invoice(accounting_export=accounting_export)

    return created_purchase_invoice


def check_accounting_export_and_start_import(workspace_id: int,  accounting_export_ids: List[str]):
    """
    Check accounting export group and start export
    """

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    accounting_exports = AccountingExport.objects.filter(
        status='ENQUEUED',
        workspace_id=workspace_id, id__in=accounting_export_ids, purchaseinvoice__id__isnull=True,
        exported_at__isnull=True
    ).all()

    chain = Chain()

    chain.append('apps.sage300.exports.purchase_invoice.queues.import_fyle_dimensions', fyle_credentials)

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

        chain.append('apps.sage300.exports.purchase_invoice.queues.create_purchase_invoice', workspace_id, accounting_export)

        if chain.length() > 1:
            chain.run()
