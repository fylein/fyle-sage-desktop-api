from apps.mappings.models import ImportLog


def create_deps_import_log(attribute_type, workspace_id):
    """
    Create dependent import logs
    """
    import_log, _ = ImportLog.objects.update_or_create(
        workspace_id=workspace_id,
        attribute_type=attribute_type,
        defaults={
            'status': 'IN_PROGRESS'
        }
    )
    return import_log
