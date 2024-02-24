"""
Fixture configuration for import tests
"""
import pytest
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_project_mappings():
    """
    Pytest fixtue to add project mappings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail='Sage 300 Project - Direct Mail Campaign, Id - 10064',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Platform APIs',
            value='Platform APIs',
            destination_id='10081',
            detail='Sage 300 Project - Platform APIs, Id - 10081',
            active=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_cost_center_mappings():
    """
    Pytest fixtue to add cost center mappings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail='Cost Center - Direct Mail Campaign, Id - 10064',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Platform APIs',
            value='Platform APIs',
            destination_id='10081',
            detail='Cost Center - Platform APIs, Id - 10081',
            active=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_merchant_mappings():
    """
    Pytest fixture to add merchant mappings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='MERCHANT',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail='Merchant - Direct Mail Campaign, Id - 10064',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='MERCHANT',
            display_name='Platform APIs',
            value='Platform APIs',
            destination_id='10081',
            detail='Merchant - Platform APIs, Id - 10081',
            active=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_project_expense_attributes():
    """
    Pytest fixture to add project expense attributes to a workspace
    """
    for i in range(1, 110):
        ExpenseAttribute.objects.create(
            workspace_id=1,
            attribute_type='PROJECT',
            display_name='Project',
            value='Platform APIs {0}'.format(i),
            source_id='1008{0}'.format(i),
            detail='Merchant - Platform APIs, Id - 1008{0}'.format(i),
            active=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_expense_destination_attributes():
    """
    Pytest fixture to add expense & destination attributes to a workspace
    """
    ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='CATEGORY',
        display_name='Category',
        value='Test Sage',
        source_id='1008',
        detail='Merchant - Platform APIs, Id - 1008',
        active=True
    )
    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='ACCOUNT',
        display_name='Account',
        value='Test Dynamics',
        destination_id='10081',
        detail='Merchant - Platform APIs, Id - 10081',
        active=True
    )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_expense_destination_attributes_1():
    """
    Pytest fixture to add expense & destination attributes to a workspace
    """
    values = ['Internet','Meals']
    count = 0

    for value in values:
        count += 1
        ExpenseAttribute.objects.create(
            workspace_id=1,
            attribute_type='CATEGORY',
            display_name='Category',
            value= value,
            source_id='1009{0}'.format(count),
            detail='Merchant - Platform APIs, Id - 1008',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=1,
            attribute_type='ACCOUNT',
            display_name='Account',
            value= value,
            destination_id=value,
            detail='Merchant - Platform APIs, Id - 10081',
            active=True
        )
