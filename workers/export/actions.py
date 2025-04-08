import logging
import os
from typing import Dict

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sage_desktop_api.settings")
django.setup()


# flake8: noqa
from apps.fyle.tasks import import_expenses
from apps.accounting_exports.models import AccountingExport


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_exports(data: Dict) -> None:
    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=data['workspace_id'],
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'ENQUEUED'
        }
    )
    data['accounting_export_id'] = accounting_export.id

    import_expenses(**data)
