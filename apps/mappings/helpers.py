
# from datetime import datetime

# from django_q.models import Schedule

# from fyle_accounting_mappings.models import MappingSetting
# from apps.fyle.models import DependentFieldSetting


# def schedule_or_delete_fyle_import_tasks(workspace_id: int):
#     """
#     :param configuration: Workspace Configuration Instance
#     :return: None
#     """
#     project_mapping = MappingSetting.objects.filter(
#         source_field='PROJECT',
#         workspace_id=workspace_id,
#         import_to_fyle=True
#     ).first()
#     dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

#     if project_mapping and dependent_fields:
#         start_datetime = datetime.now()
#         Schedule.objects.update_or_create(
#             func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
#             args='{}'.format(workspace_id),
#             defaults={
#                 'schedule_type': Schedule.MINUTES,
#                 'minutes': 24 * 60,
#                 'next_run': start_datetime
#             }
#         )
#     elif not (project_mapping and dependent_fields):
#         Schedule.objects.filter(
#             func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
#             args='{}'.format(workspace_id)
#         ).delete()
