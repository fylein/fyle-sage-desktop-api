from fyle_accounting_mappings.models import Mapping


def get_filtered_mapping(
    source_field: str, destination_type: str, workspace_id: int, source_value: str, source_id: str) -> Mapping:
    filters = {
        'source_type': source_field,
        'destination_type': destination_type,
        'workspace_id': workspace_id
    }

    if source_id:
        filters['source__source_id'] = source_id
    else:
        filters['source__value'] = source_value

    return Mapping.objects.filter(**filters).first()
