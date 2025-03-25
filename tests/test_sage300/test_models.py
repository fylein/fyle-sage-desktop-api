from apps.sage300.models import CostCategory
from apps.workspaces.models import ImportSetting
from fyle_accounting_mappings.models import DestinationAttribute


def test_bulk_create_or_update(
    db,
    mocker,
    create_temp_workspace,
    add_project_mappings,
    add_cost_code_mappings
):
    workspace_id = 1

    categories_gen_data = [{
        "Id": 1,
        "JobId": "10065",
        "CostCodeId": "10081",
        "Name": "Test Category 1",
        "IsActive": True
    },{
        "Id": 2,
        "JobId": "10082",
        "CostCodeId": "10081",
        "Name": "Test Category 2",
        "IsActive": True
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

    # Test create new categories with code in naming
    categories_gen_data = [{
        "Id": 3,
        "JobId": "10065",
        "CostCodeId": "10081",
        "Name": "Test Category 2",
        "IsActive": True,
        "Code": "456",
    }]

    ImportSetting.objects.filter(workspace_id=workspace_id).update(import_code_fields=['JOB', 'COST_CODE', 'COST_CATEGORY'])
    DestinationAttribute.objects.filter(workspace_id=workspace_id, destination_id='10065', attribute_type = 'JOB').update(code='10065')
    DestinationAttribute.objects.filter(workspace_id=workspace_id, destination_id='10065', attribute_type = 'COST_CODE').update(code='10065')

    categories_generator = categories_gen_data
    CostCategory.bulk_create_or_update(categories_generator, workspace_id)

    created_categories = CostCategory.objects.all()
    assert len(created_categories) == 3

    for category_data in categories_gen_data:
        category = CostCategory.objects.get(cost_category_id=category_data['Id'])
        assert category.job_id == category_data['JobId']
        assert category.cost_code_id == category_data['CostCodeId']
        assert category.name == category_data['Name']
        assert category.status == category_data['IsActive']
        assert category.cost_category_code == category_data['Code']
