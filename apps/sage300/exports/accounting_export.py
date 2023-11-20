from datetime import datetime
from django.db import transaction

from accounting_exports.models import AccountingExport
from apps.workspaces.models import ExportSetting


class AccountingDataExporter:
    """
    Base class for exporting accounting data to an external accounting system.
    Subclasses should implement the 'post' method for posting data.
    """

    body_model = None
    lineitem_model = None

    def post(self, body, lineitems):
        """
        Implement this method to post data to the external accounting system.
        """
        raise NotImplementedError("Please implement this method")

    def create_sage300_object(self, accounting_export: AccountingExport):
        """
        Create a purchase invoice in the external accounting system.

        Args:
            accounting_export (AccountingExport): The accounting export object.

        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        """

        # Retrieve export settings for the current workspace
        export_settings = ExportSetting.objects.filter(workspace_id=accounting_export.workspace_id)

        # Check and update the status of the accounting export
        if accounting_export.status not in ['IN_PROGRESS', 'COMPLETE']:
            accounting_export.status = 'IN_PROGRESS'
            accounting_export.save()
        else:
            # If the status is already 'IN_PROGRESS' or 'COMPLETE', return without further processing
            return

        try:
            with transaction.atomic():
                # Create or update the main body of the accounting object
                body_model_object = self.body_model.create_or_update_object(accounting_export)

                # Create or update line items for the accounting object
                lineitems_model_objects = self.lineitem_model.create_or_update_object(
                    accounting_export, export_settings
                )

                # Post the data to the external accounting system
                created_object = self.post(body_model_object, lineitems_model_objects)

                # Update the accounting export details
                accounting_export.detail = created_object
                accounting_export.status = 'COMPLETE'
                accounting_export.exported_at = datetime.now()

                accounting_export.save()

        except Exception as e:
            print(e)
            # Handle exceptions specific to the export process here
