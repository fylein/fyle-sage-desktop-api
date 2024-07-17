"""
Fixture configuration for all the tests
"""
from datetime import datetime, timezone

from unittest import mock
import pytest

from rest_framework.test import APIClient
from fyle.platform.platform import Platform
from fyle_rest_auth.models import User, AuthToken
from fyle_accounting_mappings.models import (
    ExpenseAttribute,
    DestinationAttribute,
    MappingSetting,
    EmployeeMapping,
    CategoryMapping,
    Mapping
)

from apps.fyle.helpers import get_access_token
from apps.workspaces.models import (
    Workspace,
    FyleCredential,
    Sage300Credential,
    ExportSetting,
    ImportSetting,
    AdvancedSetting
)
from apps.fyle.models import ExpenseFilter, DependentFieldSetting, Expense
from apps.accounting_exports.models import AccountingExport, Error, AccountingExportSummary
from sage_desktop_api.tests import settings
from apps.sage300.models import CostCategory
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.sage300.exports.direct_cost.models import DirectCost

from .test_fyle.fixtures import fixtures as fyle_fixtures


@pytest.fixture
def api_client():
    """
    Fixture required to test views
    """
    return APIClient()


@pytest.fixture()
def test_connection(db):
    """
    Creates a connection with Fyle
    """
    client_id = settings.FYLE_CLIENT_ID
    client_secret = settings.FYLE_CLIENT_SECRET
    token_url = settings.FYLE_TOKEN_URI
    refresh_token = 'Dummy.Refresh.Token'
    server_url = settings.FYLE_BASE_URL

    fyle_connection = Platform(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        server_url=server_url
    )

    access_token = get_access_token(refresh_token)
    fyle_connection.access_token = access_token
    user_profile = fyle_connection.v1beta.spender.my_profile.get()['data']
    user = User(
        password='', last_login=datetime.now(tz=timezone.utc), id=1, email=user_profile['user']['email'],
        user_id=user_profile['user_id'], full_name='', active='t', staff='f', admin='t'
    )

    user.save()

    auth_token = AuthToken(
        id=1,
        refresh_token=refresh_token,
        user=user
    )
    auth_token.save()

    return fyle_connection


@pytest.fixture(scope="session", autouse=True)
def default_session_fixture(request):
    patched_1 = mock.patch(
        'fyle_rest_auth.authentication.get_fyle_admin',
        return_value=fyle_fixtures['get_my_profile']
    )
    patched_1.__enter__()

    patched_2 = mock.patch(
        'fyle.platform.internals.auth.Auth.update_access_token',
        return_value='asnfalsnkflanskflansfklsan'
    )
    patched_2.__enter__()

    patched_3 = mock.patch(
        'apps.fyle.helpers.post_request',
        return_value={
            'access_token': 'easnfkjo12233.asnfaosnfa.absfjoabsfjk',
            'cluster_domain': 'https://staging.fyle.tech'
        }
    )
    patched_3.__enter__()

    patched_4 = mock.patch(
        'fyle.platform.apis.v1beta.spender.MyProfile.get',
        return_value=fyle_fixtures['get_my_profile']
    )
    patched_4.__enter__()

    patched_5 = mock.patch(
        'fyle_rest_auth.helpers.get_fyle_admin',
        return_value=fyle_fixtures['get_my_profile']
    )
    patched_5.__enter__()


@pytest.fixture
@pytest.mark.django_db(databases=['default'])
def create_temp_workspace():
    """
    Pytest fixture to create a temorary workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        Workspace.objects.create(
            id=workspace_id,
            name='Fyle For Testing {}'.format(workspace_id),
            org_id='riseabovehate{}'.format(workspace_id),
            reimbursable_last_synced_at=None,
            credit_card_last_synced_at=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc)
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_fyle_credentials():
    """
    Pytest fixture to add fyle credentials to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        FyleCredential.objects.create(
            refresh_token='dummy_refresh_token',
            workspace_id=workspace_id,
            cluster_domain='https://dummy_cluster_domain.com',
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_sage300_creds():
    """
    Pytest fixture to add fyle credentials to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        Sage300Credential.objects.create(
            identifier='identifier',
            username='username',
            password='password',
            workspace_id=workspace_id,
            api_key='apiley',
            api_secret='apisecret'
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_expense_filters():
    """
    Pytest fixture to add expense filters to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        ExpenseFilter.objects.create(
            condition='employee_email',
            operator='in',
            values=['ashwinnnnn.t@fyle.in', 'admin1@fyleforleaf.in'],
            rank="1",
            join_by='AND',
            is_custom=False,
            custom_field_type='SELECT',
            workspace_id=workspace_id
        )
        ExpenseFilter.objects.create(
            condition='last_spent_at',
            operator='lt',
            values=['2020-04-20 23:59:59+00'],
            rank="2",
            join_by=None,
            is_custom=False,
            custom_field_type='SELECT',
            workspace_id=workspace_id
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_accounting_export_expenses():
    """
    Pytest fixture to add accounting export to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        AccountingExport.objects.update_or_create(
            workspace_id=workspace_id,
            type='FETCHING_REIMBURSABLE_EXPENSES',
            defaults={
                'status': 'IN_PROGRESS'
            }
        )

        AccountingExport.objects.update_or_create(
            workspace_id=workspace_id,
            type='FETCHING_CREDIT_CARD_EXPENENSES',
            defaults={
                'status': 'IN_PROGRESS'
            }
        )

        AccountingExport.objects.update_or_create(
            workspace_id=workspace_id,
            type='PURCHASE_INVOICE',
            defaults={
                'status': 'EXPORT_QUEUED',
                'detail': {'export_id': '123'},
                'export_id': 1234
            }
        )

        AccountingExport.objects.update_or_create(
            workspace_id=workspace_id,
            type='DIRECT_COST',
            defaults={
                'status': 'EXPORT_QUEUED',
                'detail': {'export_id': '123'},
                'export_id': 1234
            }
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_errors():
    """
    Pytest fixture to add errors to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        Error.objects.create(
            type='EMPLOYEE_MAPPING',
            is_resolved=False,
            error_title='Employee Mapping Error',
            error_detail='Employee Mapping Error',
            workspace_id=workspace_id
        )
        Error.objects.create(
            type='CATEGORY_MAPPING',
            is_resolved=False,
            error_title='Category Mapping Error',
            error_detail='Category Mapping Error',
            workspace_id=workspace_id
        )
        Error.objects.create(
            type='SAGE300_ERROR',
            is_resolved=False,
            error_title='Sage Error',
            error_detail='Sage Error',
            workspace_id=workspace_id
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_accounting_export_summary():
    """
    Pytest fixture to add accounting export summary to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        AccountingExportSummary.objects.create(
            workspace_id=workspace_id,
            last_exported_at = datetime.now(tz=timezone.utc),
            next_export_at = datetime.now(tz=timezone.utc),
            export_mode = 'AUTO',
            total_accounting_export_count = 10,
            successful_accounting_export_count = 5,
            failed_accounting_export_count = 5
        )


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
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='JOB',
            display_name='CRE Platform',
            value='CRE Platform',
            destination_id='10064',
            detail='Sage 300 Project - CRE Platform, Id - 10064',
            active=True,
            code='123'
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='JOB',
            display_name='Integrations CRE',
            value='Integrations CRE',
            destination_id='10081',
            detail='Sage 300 Project - Integrations CRE, Id - 10081',
            active=True,
            code='123'
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            source_id='10064',
            detail='Sage 300 Project - Direct Mail Campaign, Id - 10064',
            active=True
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Platform APIs',
            value='Platform APIs',
            source_id='10081',
            detail='Sage 300 Project - Platform APIs, Id - 10081',
            active=True
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='CRE Platform',
            value='123 CRE Platform',
            source_id='10065',
            detail='Sage 300 Project - 123 CRE Platform, Id - 10065',
            active=True
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Integrations CRE',
            value='123 Integrations CRE',
            source_id='10082',
            detail='Sage 300 Project - 123 Integrations CRE, Id - 10082',
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
def add_cost_code_mappings():
    """
    Pytest fixtue to add cost center mappings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CODE',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail='Cost Center - Direct Mail Campaign, Id - 10064',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CODE',
            display_name='Platform APIs',
            value='Platform APIs',
            destination_id='10081',
            detail='Cost Center - Platform APIs, Id - 10081',
            active=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_export_settings():
    """
    Pytest fixtue to add export_settings to a workspace
    """

    workspace_ids = [
        1, 2, 3
    ]

    for workspace_id in workspace_ids:
        ExportSetting.objects.create(
            workspace_id=workspace_id,
            reimbursable_expenses_export_type='PURCHASE_INVOICE' if workspace_id in [1, 2] else 'DIRECT_COST',
            default_bank_account_name='Accounts Payable',
            default_back_account_id='1',
            reimbursable_expense_state='PAYMENT_PROCESSING',
            reimbursable_expense_date='SPENT_AT' if workspace_id == 1 else 'LAST_SPENT_AT',
            reimbursable_expense_grouped_by='REPORT' if workspace_id == 1 else 'EXPENSE',
            credit_card_expense_export_type='DIRECT_COST' if workspace_id in [1, 2] else 'PURCHASE_INVOICE',
            credit_card_expense_state='PAYMENT_PROCESSING',
            default_ccc_credit_card_account_name='Visa',
            default_ccc_credit_card_account_id='12',
            credit_card_expense_grouped_by='EXPENSE' if workspace_id == 3 else 'REPORT',
            credit_card_expense_date='SPENT_AT',
            default_vendor_id='1',
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_import_settings():
    """
    Pytest fixtue to add export_settings to a workspace
    """

    workspace_ids = [
        1, 2, 3
    ]

    for workspace_id in workspace_ids:
        ImportSetting.objects.create(
            workspace_id=workspace_id,
            import_categories=False,
            import_vendors_as_merchants=False,
            import_code_fields = []
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_project_mapping_settings():
    """
    Pytest fixture to add merchant mappings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        MappingSetting.objects.create(
            workspace_id=workspace_id,
            source_field='PROJECT',
            destination_field='PROJECT',
            import_to_fyle=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_advanced_settings():
    advanced_settings_data = fyle_fixtures['advanced_setting']
    AdvancedSetting.objects.create(**advanced_settings_data)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_expense_attribute():
    expense_attribute_data = fyle_fixtures['employee_expense_attributes']
    expense_attribute_data['workspace'] = Workspace.objects.get(id=1)
    expense_attribute = ExpenseAttribute.objects.create(**expense_attribute_data)

    return expense_attribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_destination_attribute():
    destination_emp_data = fyle_fixtures['employee_destination_attributes']
    destination_emp_data['workspace'] = Workspace.objects.get(id=1)
    DestinationAttribute.objects.create(**destination_emp_data)

    destination_vendor_data = fyle_fixtures['vendor_destination_attributes']
    destination_vendor_data['workspace'] = Workspace.objects.get(id=1)
    DestinationAttribute.objects.create(**destination_vendor_data)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_employee_mapping_with_employee(create_expense_attribute, create_destination_attribute):
    source_field_id = ExpenseAttribute.objects.get(source_id='source123')
    destination_field_id = DestinationAttribute.objects.get(destination_id='destination123')
    workspace = Workspace.objects.get(id=1)

    employee_employee_mapping = {
        'source_employee': source_field_id,
        'destination_employee': destination_field_id,
        'workspace': workspace,
    }

    EmployeeMapping.objects.create(**employee_employee_mapping)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_employee_mapping_with_vendor(create_expense_attribute, create_destination_attribute):
    source_field_id = ExpenseAttribute.objects.get(source_id='source123')
    destination_field_id = DestinationAttribute.objects.get(destination_id='dest_vendor123')
    workspace = Workspace.objects.get(id=1)

    employee_vendor_mapping = {
        'source_employee': source_field_id,
        'destination_vendor': destination_field_id,
        'workspace': workspace,
    }

    EmployeeMapping.objects.create(**employee_vendor_mapping)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_source_category_attribute():
    source_category_attribute_data = fyle_fixtures['category_expense_attributes']
    source_category_attribute_data['workspace'] = Workspace.objects.get(id=1)
    source_category_attribute = ExpenseAttribute.objects.create(**source_category_attribute_data)

    return source_category_attribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_destination_category_attribute():
    destination_category_attribute_data = fyle_fixtures['category_destination_attributes']
    destination_category_attribute_data['workspace'] = Workspace.objects.get(id=1)
    destination_category_attribute = DestinationAttribute.objects.create(**destination_category_attribute_data)

    return destination_category_attribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_category_mapping(create_source_category_attribute, create_destination_category_attribute):
    source_category = ExpenseAttribute.objects.get(source_id='src_category123')
    destination_category = DestinationAttribute.objects.get(destination_id='dest_category123')
    workspace = Workspace.objects.get(id=1)

    category_mapping = CategoryMapping.create_or_update_category_mapping(
        source_category_id=source_category.id,
        destination_account_id=destination_category.id,
        workspace=workspace
    )

    return category_mapping


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_cost_category(create_temp_workspace):
    """
    Pytest fixture to add cost category to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        CostCategory.objects.create(
            job_id='10064',
            job_name='Platform APIs',
            cost_code_id='cost_code_id',
            cost_code_name='Platform APIs',
            name='API',
            cost_category_id='cost_category_id',
            status=True,
            workspace = Workspace.objects.get(id=workspace_id),
            is_imported = False
        )
        CostCategory.objects.create(
            job_id='10081',
            job_name='Direct Mail Campaign',
            cost_code_id='cost_code_id',
            cost_code_name='Direct Mail Campaign',
            name='Mail',
            cost_category_id='cost_category_id',
            status=True,
            workspace = Workspace.objects.get(id=workspace_id),
            is_imported = False
        )
        CostCategory.objects.create(
            job_id='10065',
            job_name='Integrations CRE',
            cost_code_id='cost_code_id_123',
            cost_code_name='Integrations CRE',
            name='Integrations',
            cost_category_id='cost_category_id_456',
            status=True,
            workspace = Workspace.objects.get(id=workspace_id),
            is_imported = False
        )
        CostCategory.objects.create(
            job_id='10082',
            job_name='CRE Platform',
            cost_code_id='cost_code_id_545',
            cost_code_name='CRE Platform',
            name='CRE',
            cost_category_id='cost_category_id_583',
            status=True,
            workspace = Workspace.objects.get(id=workspace_id),
            is_imported = False
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_dependent_field_setting(create_temp_workspace):
    """
    Pytest fixture to add dependent fields to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]

    for workspace_id in workspace_ids:
        DependentFieldSetting.objects.create(
            is_import_enabled=True,
            project_field_id=1,
            cost_code_field_name='Cost Code',
            cost_code_field_id='cost_code',
            cost_code_placeholder='Select Cost Code',
            cost_category_field_name='Cost Category',
            cost_category_field_id='cost_category',
            cost_category_placeholder='Select Cost Category',
            workspace=Workspace.objects.get(id=workspace_id)
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_mapping_object(
    create_temp_workspace,
    create_expense_attribute,
    create_destination_attribute
):
    workspace_id = 1
    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()
    destination_attribute = DestinationAttribute.objects.filter(workspace_id=workspace_id).first()
    workspace = Workspace.objects.get(id=workspace_id)

    mapping_object = Mapping.objects.create(
        source_type=expense_attribute.attribute_type,
        destination_type=destination_attribute.attribute_type,
        source=expense_attribute,
        destination=destination_attribute,
        workspace=workspace
    )

    return mapping_object


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_expense_objects():
    workspace_id = 1
    expenses = fyle_fixtures['expenses']
    expense_objects = Expense.create_expense_objects(expenses=expenses, workspace_id=workspace_id)

    return expense_objects


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_purchase_invoice_objects(
    create_temp_workspace,
    add_fyle_credentials,
    add_accounting_export_expenses,
    add_advanced_settings,
    add_export_settings,
):
    accounting_export = AccountingExport.objects.get(workspace_id=1, type='PURCHASE_INVOICE')
    accounting_export.description = {'fund_source': 'PERSONAL', 'employee_email': 'jhonsnow@fyle.in'}
    accounting_export.save()

    PurchaseInvoice.create_or_update_object(
        accounting_export=accounting_export,
        advance_settings=AdvancedSetting.objects.get(workspace_id=1)
    )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_purchase_invoice_lineitem_objects(
    add_purchase_invoice_objects,
    create_expense_objects,
    add_cost_category,
    create_category_mapping,
    add_dependent_field_setting
):
    workspace_id = 1

    account = CategoryMapping.objects.filter(
        workspace_id=workspace_id
    ).first()

    account.source_category.value = 'Accounts Payable'
    account.source_category.save()
    account.save()

    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id, type='PURCHASE_INVOICE')
    expense = Expense.objects.get(workspace_id=workspace_id)
    accounting_export.expenses.set([expense])
    accounting_export.save()

    PurchaseInvoiceLineitems.create_or_update_object(
        accounting_export=accounting_export,
        advance_setting=AdvancedSetting.objects.get(workspace_id=1)
    )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_direct_cost_objects(
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_accounting_export_expenses,
    add_advanced_settings,
    add_export_settings,
    add_cost_category,
    create_expense_objects,
    create_category_mapping,
    add_dependent_field_setting
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id, type='DIRECT_COST')
    accounting_export.expenses.set(Expense.objects.filter(workspace_id=workspace_id))
    accounting_export.description = {'fund_source': 'PERSONAL', 'employee_email': 'jhonsnow@fyle.in'}
    accounting_export.save()

    account = CategoryMapping.objects.filter(
        workspace_id=accounting_export.workspace_id
    ).first()
    account.source_category.value = 'Accounts Payable'
    account.source_category.save()
    account.save()

    DirectCost.create_or_update_object(
        accounting_export=accounting_export,
        advance_setting=AdvancedSetting.objects.get(workspace_id=1)
    )
