# from fyle_accounting_mappings.models import MappingSetting

# from apps.fyle.models import DependentFieldSetting
# from apps.workspaces.models import ExportSetting


# def schedule_or_delete_dependent_fields(export_settings: ExportSetting):
#     """
#     :param export_settings: ExportSetting Configuration Instance
#     :return: None
#     """

#     project_mapping = MappingSetting.objects.filter(
#         source_field='PROJECT',
#         workspace_id=export_settings.workspace_id,
#         import_to_fyle=True
#     ).first()
#     dependent_fields = DependentFieldSetting.objects.filter(workspace_id=export_settings.workspace_id, is_import_enabled=True).first()
    