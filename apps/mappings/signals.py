import logging
from datetime import timedelta, datetime, timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from rest_framework.exceptions import ValidationError
from fyle_accounting_mappings.models import MappingSetting, CategoryMapping
from fyle_integrations_platform_connector import PlatformConnector
from fyle.platform.exceptions import WrongParamsError

from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks
from apps.workspaces.models import ImportSetting
from apps.accounting_exports.models import Error
from apps.mappings.models import ImportLog
from apps.workspaces.models import FyleCredential
from apps.mappings.imports.modules.expense_custom_fields import ExpenseCustomField


logger = logging.getLogger(__name__)


@receiver(post_save, sender=MappingSetting)
def run_post_mapping_settings_triggers(sender, instance: MappingSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    import_settings = ImportSetting.objects.filter(workspace_id=instance.workspace_id).first()

    if instance.source_field == 'PROJECT':
        schedule_or_delete_fyle_import_tasks(import_settings, instance)

    if instance.source_field == 'COST_CENTER':
        schedule_or_delete_fyle_import_tasks(import_settings, instance)

    if instance.is_custom:
        schedule_or_delete_fyle_import_tasks(import_settings, instance)


@receiver(pre_save, sender=MappingSetting)
def run_pre_mapping_settings_triggers(sender, instance: MappingSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    default_attributes = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER']

    instance.source_field = instance.source_field.upper().replace(' ', '_')

    if instance.source_field not in default_attributes and instance.import_to_fyle:
        # TODO: sync sage 300 fields before we upload custom field
        try:
            workspace_id = int(instance.workspace_id)
            # Checking is import_log exists or not if not create one
            import_log, is_created = ImportLog.objects.get_or_create(
                workspace_id=workspace_id,
                attribute_type=instance.source_field,
                defaults={
                    'status': 'IN_PROGRESS'
                }
            )

            last_successful_run_at = None
            if import_log and not is_created:
                last_successful_run_at = import_log.last_successful_run_at if import_log.last_successful_run_at else None
                time_difference = datetime.now() - timedelta(minutes=32)
                offset_aware_time_difference = time_difference.replace(tzinfo=timezone.utc)

                # if the import_log is present and the last_successful_run_at is less than 30mins then we need to update it
                # so that the schedule can run
                if last_successful_run_at and offset_aware_time_difference\
                    and (offset_aware_time_difference < last_successful_run_at):
                    import_log.last_successful_run_at = offset_aware_time_difference
                    last_successful_run_at = offset_aware_time_difference
                    import_log.save()

            # Creating the expense_custom_field object with the correct last_successful_run_at value
            expense_custom_field = ExpenseCustomField(
                workspace_id=workspace_id,
                source_field=instance.source_field,
                destination_field=instance.destination_field,
                sync_after=last_successful_run_at
            )

            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            platform = PlatformConnector(fyle_credentials=fyle_credentials)

            # setting the import_log status to IN_PROGRESS
            import_log.status = 'IN_PROGRESS'
            import_log.save()

            expense_custom_field.construct_payload_and_import_to_fyle(platform, import_log)
            expense_custom_field.sync_expense_attributes(platform)

            # NOTE: We are not setting the import_log status to COMPLETE
            # since the post_save trigger will run the import again in async manner

        except WrongParamsError as error:
            logger.error(
                'Error while creating %s workspace_id - %s in Fyle %s %s',
                instance.source_field, instance.workspace_id, error.message, {'error': error.response}
            )
            if error.response and 'message' in error.response:
                raise ValidationError({
                    'message': error.response['message'],
                    'field_name': instance.source_field
                })

        # setting the import_log.last_successful_run_at to -30mins for the post_save_trigger
        import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=instance.source_field).first()
        if import_log.last_successful_run_at:
            last_successful_run_at = import_log.last_successful_run_at - timedelta(minutes=30)
            import_log.last_successful_run_at = last_successful_run_at
            import_log.save()


@receiver(post_save, sender=CategoryMapping)
def resolve_post_category_mapping_errors(sender, instance: CategoryMapping, **kwargs):
    """
    Resolve errors after mapping is created
    """
    Error.objects.filter(expense_attribute_id=instance.source_category).update(
        is_resolved=True
    )
