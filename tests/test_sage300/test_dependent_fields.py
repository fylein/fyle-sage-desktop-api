from apps.sage300.dependent_fields import (
    construct_custom_field_placeholder,
    post_dependent_cost_code,
    post_dependent_cost_type,
    post_dependent_expense_field_values,
    import_dependent_fields_to_fyle
)
from apps.fyle.models import DependentFieldSetting
from apps.mappings.helpers import create_deps_import_log


def test_construct_custom_field_placeholder():
    source_placeholder = "Source Placeholder"
    fyle_attribute = "Fyle Attribute"
    existing_attribute = {
        "placeholder": "Existing Placeholder"
    }

    expected_result = "Source Placeholder"
    result = construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result

    source_placeholder = None
    existing_attribute = {
        "placeholder": "Existing Placeholder"
    }

    expected_result = "Existing Placeholder"
    result = construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result

    source_placeholder = "Source Placeholder"
    existing_attribute = None

    expected_result = "Source Placeholder"
    result = construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result

    source_placeholder = None
    existing_attribute = None

    expected_result = "Select Fyle Attribute"
    result = construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result


def test_post_dependent_cost_code(
    db,
    mocker,
    create_temp_workspace,
    add_cost_category,
    add_dependent_field_setting,
    add_project_mappings
):
    workspace_id = 1

    platform = mocker.patch('apps.sage300.dependent_fields.PlatformConnector')
    mocker.patch.object(
        platform.return_value,
        'dependent_fields.bulk_post_dependent_expense_field_values'
    )

    filters = {
        "workspace_id": workspace_id
    }

    dependent_field_settings = DependentFieldSetting.objects.get(workspace_id=workspace_id)
    cost_code_import_log = create_deps_import_log('COST_CODE', workspace_id)

    result = post_dependent_cost_code(
        cost_code_import_log,
        dependent_field_setting=dependent_field_settings,
        platform=platform.return_value,
        filters=filters
    )

    assert result == ['Direct Mail Campaign', 'Platform APIs']


def test_post_dependent_cost_type(
    db,
    mocker,
    create_temp_workspace,
    add_cost_category,
    add_dependent_field_setting,
    add_project_mappings
):
    workspace_id = 1

    platform = mocker.patch('apps.sage300.dependent_fields.PlatformConnector')
    mocker.patch.object(
        platform.return_value,
        'dependent_fields.bulk_post_dependent_expense_field_values'
    )

    filters = {
        "workspace_id": workspace_id
    }

    dependent_field_settings = DependentFieldSetting.objects.get(workspace_id=workspace_id)

    cost_category_import_log = create_deps_import_log('COST_CATEGORY', workspace_id)

    post_dependent_cost_type(
        cost_category_import_log,
        dependent_field_setting=dependent_field_settings,
        platform=platform.return_value,
        filters=filters
    )

    assert platform.return_value.dependent_fields.bulk_post_dependent_expense_field_values.call_count == 2


def test_post_dependent_expense_field_values(
    db,
    mocker,
    create_temp_workspace,
    add_cost_category,
    add_dependent_field_setting,
    add_project_mappings
):
    workspace_id = 1

    platform = mocker.patch('apps.sage300.dependent_fields.PlatformConnector')
    mocker.patch('apps.sage300.dependent_fields.connect_to_platform', return_value=platform.return_value)
    mocker.patch.object(
        platform.return_value,
        'dependent_fields.bulk_post_dependent_expense_field_values'
    )

    dependent_field_settings = DependentFieldSetting.objects.get(workspace_id=workspace_id)

    create_deps_import_log('COST_CODE', workspace_id)
    create_deps_import_log('COST_CATEGORY', workspace_id)

    post_dependent_expense_field_values(
        workspace_id=workspace_id,
        dependent_field_setting=dependent_field_settings
    )

    assert platform.return_value.dependent_fields.bulk_post_dependent_expense_field_values.call_count == 4
    assert DependentFieldSetting.objects.get(workspace_id=workspace_id).last_successful_import_at is not None


def test_import_dependent_fields_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_cost_category,
    add_dependent_field_setting,
    add_project_mappings
):
    workspace_id = 1

    platform = mocker.patch('apps.sage300.dependent_fields.PlatformConnector')
    mocker.patch('apps.sage300.dependent_fields.connect_to_platform', return_value=platform.return_value)
    mocker.patch.object(
        platform.return_value,
        'dependent_fields.bulk_post_dependent_expense_field_values'
    )

    create_deps_import_log('COST_CODE', workspace_id)
    create_deps_import_log('COST_CATEGORY', workspace_id)

    import_dependent_fields_to_fyle(workspace_id)

    assert platform.return_value.dependent_fields.bulk_post_dependent_expense_field_values.call_count == 4
    assert DependentFieldSetting.objects.get(workspace_id=workspace_id).last_successful_import_at is not None
