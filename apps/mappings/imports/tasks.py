from django_q.tasks import Chain

from fyle_accounting_mappings.models import MappingSetting

from apps.mappings.models import ImportLog
from apps.mappings.imports.modules.categories import Category
from apps.mappings.imports.modules.projects import Project
from apps.mappings.imports.modules.expense_custom_fields import ExpenseCustomField
from apps.fyle.models import DependentFieldSetting


SOURCE_FIELD_CLASS_MAP = {
    'CATEGORY': Category,
    'PROJECT': Project
}


def trigger_import_via_schedule(workspace_id: int, destination_field: str, source_field: str, is_custom: bool = False):
    """
    Trigger import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    :param source_field: Type of attribute (e.g., 'PROJECT', 'CATEGORY', 'COST_CENTER')
    """
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=source_field).first()
    sync_after = import_log.last_successful_run_at if import_log else None

    if is_custom:
        item = ExpenseCustomField(workspace_id, source_field, destination_field, sync_after)
        item.trigger_import()
    else:
        module_class = SOURCE_FIELD_CLASS_MAP[source_field]
        item = module_class(workspace_id, destination_field, sync_after)
        item.trigger_import()


def auto_import_and_map_fyle_fields(workspace_id):
    """
    Auto import and map fyle fields
    """
    project_mapping = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True
    ).first()
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    chain = Chain()

    if project_mapping and dependent_fields:
        chain.append('apps.sage_300.dependent_fields.import_dependent_fields_to_fyle', workspace_id)

    if chain.length() > 0:
        chain.run()
