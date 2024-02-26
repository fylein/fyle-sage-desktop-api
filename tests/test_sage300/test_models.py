from apps.sage300.models import CostCategory
from sage_desktop_sdk.core.schema.read_only import Category


def test_bulk_create_or_update(
    db,
    mocker,
    create_temp_workspace,
    add_project_mappings
):
    workspace_id = 1

    mock_category = mocker.Mock(spec=Category)
    mock_category.id = 1
    mock_category.job_id = '10064'
    mock_category.cost_code_id = '10064'
    mock_category.name = 'Test Category 1'
    mock_category.is_active = True

    mock_category2 = mocker.Mock(spec=Category)
    mock_category2.id = 2
    mock_category2.job_id = '10081'
    mock_category2.cost_code_id = '10064'
    mock_category2.name = 'Test Category 2'
    mock_category2.is_active = False

    categories_generator = [mock_category, mock_category2]

    CostCategory.bulk_create_or_update(categories_generator, workspace_id)

    created_categories = CostCategory.objects.all()
    assert len(created_categories) == 2

    for category_data in categories_generator:
        category = CostCategory.objects.get(cost_category_id=category_data.id)
        assert category.job_id == category_data.job_id
        assert category.cost_code_id == category_data.cost_code_id
        assert category.name == category_data.name
        assert category.status == category_data.is_active
