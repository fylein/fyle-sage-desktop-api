from apps.sage300.models import CostCategory


def test_bulk_create_or_update(
    db,
    mocker,
    create_temp_workspace,
    add_project_mappings
):
    workspace_id = 1

    categories_gen_data = [{
        "Id": 1,
        "JobId": "10064",
        "CostCodeId": "10064",
        "Name": "Test Category 1",
        "IsActive": True
    },{
        "Id": 2,
        "JobId": "10081",
        "CostCodeId": "10064",
        "Name": "Test Category 2",
        "IsActive": False
    }]

    categories_generator = categories_gen_data

    CostCategory.bulk_create_or_update(categories_generator, workspace_id)

    created_categories = CostCategory.objects.all()
    assert len(created_categories) == 2

    for category_data in categories_gen_data:
        category = CostCategory.objects.get(cost_category_id=category_data['Id'])
        assert category.job_id == category_data['JobId']
        assert category.cost_code_id == category_data['CostCodeId']
        assert category.name == category_data['Name']
        assert category.status == category_data['IsActive']
